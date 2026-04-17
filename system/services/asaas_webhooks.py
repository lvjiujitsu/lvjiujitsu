import logging

from django.db import transaction
from django.db.utils import OperationalError
from django.utils import timezone

from system.models.asaas import (
    AsaasWebhookEvent,
    PayoutStatus,
    TeacherPayout,
)
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.services.asaas_payroll import mark_payout_failed, mark_payout_paid
from system.services.financial_transactions import apply_order_financials
from system.services.membership import activate_membership_from_paid_order


logger = logging.getLogger(__name__)


PAYMENT_RECEIVED_EVENTS = {
    "PAYMENT_CONFIRMED",
    "PAYMENT_RECEIVED",
}

PAYMENT_FAILURE_EVENTS = {
    "PAYMENT_OVERDUE",
    "PAYMENT_DELETED",
    "PAYMENT_REFUND_REQUESTED",
    "PAYMENT_CHARGEBACK_REQUESTED",
    "PAYMENT_CHARGEBACK_DISPUTE",
}

TRANSFER_SUCCESS_EVENTS = {
    "TRANSFER_DONE",
    "TRANSFER_PAID",
    "TRANSFER_CONFIRMED",
}

TRANSFER_FAILURE_EVENTS = {
    "TRANSFER_FAILED",
    "TRANSFER_CANCELLED",
    "TRANSFER_DENIED",
}

ACTIONABLE_PAYMENT_EVENTS = PAYMENT_RECEIVED_EVENTS | PAYMENT_FAILURE_EVENTS
ACTIONABLE_TRANSFER_EVENTS = TRANSFER_SUCCESS_EVENTS | TRANSFER_FAILURE_EVENTS


@transaction.atomic
def process_asaas_event(event: dict):
    """Idempotente. Retorna dict com {order, payout, duplicate}."""
    event_id = event.get("id") or ""
    event_type = event.get("event") or ""
    if not event_id:
        logger.warning("Webhook Asaas sem id — ignorando")
        return {"order": None, "payout": None, "duplicate": False}

    order = None
    payout = None

    if event_type.startswith("PAYMENT_"):
        if event_type not in ACTIONABLE_PAYMENT_EVENTS:
            return {"order": None, "payout": None, "duplicate": False}
    elif event_type.startswith("TRANSFER_"):
        if event_type not in ACTIONABLE_TRANSFER_EVENTS:
            return {"order": None, "payout": None, "duplicate": False}

    existing = AsaasWebhookEvent.objects.filter(event_id=event_id).first()
    if existing is not None:
        return {
            "order": existing.order,
            "payout": existing.payout,
            "duplicate": True,
        }

    if event_type.startswith("PAYMENT_"):
        order = _handle_payment_event(event_type, event)
    elif event_type.startswith("TRANSFER_"):
        payout = _handle_transfer_event(event_type, event)

    try:
        AsaasWebhookEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            order=order,
            payout=payout,
            payload=event,
        )
    except OperationalError as exc:
        if "database is locked" in str(exc).lower():
            logger.warning(
                "SQLite lock ao registrar evento Asaas %s; continuando sem log.",
                event_id,
            )
        else:
            raise
    return {"order": order, "payout": payout, "duplicate": False}


def _handle_payment_event(event_type, event):
    payment = event.get("payment") or {}
    asaas_payment_id = payment.get("id")
    if not asaas_payment_id:
        return None

    order = RegistrationOrder.objects.filter(
        asaas_payment_id=asaas_payment_id
    ).first()
    if order is None:
        external_ref = payment.get("externalReference")
        if external_ref:
            try:
                order = RegistrationOrder.objects.filter(pk=int(external_ref)).first()
            except (ValueError, TypeError):
                order = None
    if order is None:
        return None

    if event_type in PAYMENT_RECEIVED_EVENTS:
        if order.payment_status not in (
            PaymentStatus.PAID,
            PaymentStatus.EXEMPTED,
            PaymentStatus.REFUNDED,
        ):
            order.payment_status = PaymentStatus.PAID
            order.paid_at = timezone.now()
            order.save(
                update_fields=["payment_status", "paid_at", "updated_at"]
            )
        apply_order_financials(
            order,
            financial_transaction_id=asaas_payment_id,
            mark_available=True,
        )
        activate_membership_from_paid_order(
            order,
            notes="Pagamento confirmado via Asaas.",
        )
    elif event_type in PAYMENT_FAILURE_EVENTS:
        if order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.FAILED
            order.save(update_fields=["payment_status", "updated_at"])
    return order


def _handle_transfer_event(event_type, event):
    transfer = event.get("transfer") or {}
    transfer_id = transfer.get("id")
    if not transfer_id:
        return None

    payout = TeacherPayout.objects.filter(asaas_transfer_id=transfer_id).first()
    if payout is None:
        external_ref = transfer.get("externalReference") or ""
        if external_ref.startswith("payout-"):
            try:
                payout_pk = int(external_ref.split("-", 1)[1])
                payout = TeacherPayout.objects.filter(pk=payout_pk).first()
            except (ValueError, IndexError):
                payout = None
    if payout is None:
        return None

    if event_type in TRANSFER_SUCCESS_EVENTS:
        if payout.status != PayoutStatus.PAID:
            mark_payout_paid(payout)
    elif event_type in TRANSFER_FAILURE_EVENTS:
        if not payout.is_terminal:
            reason = transfer.get("failReason") or event_type
            mark_payout_failed(payout, reason=reason)
    return payout
