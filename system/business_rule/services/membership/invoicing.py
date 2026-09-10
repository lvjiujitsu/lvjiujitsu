import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from system.business_rule.models.membership import Membership, MembershipInvoice, MembershipStatus
from system.business_rule.models.registration_order import PaymentStatus, RegistrationOrder
from system.business_rule.services.payroll_rules import append_order_refund_record
from system.business_rule.runtime_config import payment_currency
from system.business_rule.services.stripe_notifications import notify_payment_failed
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.services.family_pricing import recompute_family_discounts_for_person
from system.business_rule.models.membership_timeline import MembershipTimelineEventType
from system.business_rule.services.membership.cycles import from_unix
from system.business_rule.services.membership.stripe_gateway import stripe_get

logger = logging.getLogger(__name__)


@transaction.atomic
def record_invoice_from_stripe(stripe_invoice):
    subscription_id = stripe_get(stripe_invoice, "subscription")
    if not subscription_id:
        return None
    memberships = list(
        Membership.objects.filter(stripe_subscription_id=str(subscription_id))
    )
    if not memberships:
        return None

    invoice_id = stripe_invoice["id"]
    lines = stripe_get(stripe_invoice, "lines")
    line_data = stripe_get(lines, "data") if lines is not None else None

    status_transitions = stripe_get(stripe_invoice, "status_transitions")
    paid_at_unix = stripe_get(status_transitions, "paid_at") if status_transitions is not None else None
    common = {
        "currency": stripe_get(stripe_invoice, "currency", payment_currency()) or payment_currency(),
        "status": stripe_get(stripe_invoice, "status", "paid") or "paid",
        "hosted_invoice_url": stripe_get(stripe_invoice, "hosted_invoice_url", "") or "",
        "stripe_payment_intent_id": str(stripe_get(stripe_invoice, "payment_intent", "") or ""),
        "paid_at": from_unix(paid_at_unix) or timezone.now(),
        "description": (stripe_get(stripe_invoice, "description", "") or "")[:255],
    }

    if len(memberships) == 1 or not line_data:
        membership = memberships[0]
        amount_paid = Decimal(stripe_get(stripe_invoice, "amount_paid", 0) or 0) / Decimal("100")
        period_start = None
        period_end = None
        if line_data:
            period = stripe_get(line_data[0], "period")
            if period is not None:
                period_start = from_unix(stripe_get(period, "start"))
                period_end = from_unix(stripe_get(period, "end"))
        invoice, _ = MembershipInvoice.objects.update_or_create(
            stripe_invoice_id=invoice_id,
            defaults={
                "membership": membership,
                "amount_paid": amount_paid,
                "period_start": period_start,
                "period_end": period_end,
                **common,
            },
        )
        _refresh_membership_after_invoice(
            membership, invoice_id, period_start, period_end, amount_paid=amount_paid
        )
        return invoice

    memberships_by_item_id = {
        m.stripe_subscription_item_id: m for m in memberships if m.stripe_subscription_item_id
    }
    first_invoice = None
    for line in line_data:
        item_id = str(stripe_get(line, "subscription_item", "") or "")
        membership = memberships_by_item_id.get(item_id)
        if membership is None:
            continue
        line_amount = Decimal(stripe_get(line, "amount", 0) or 0) / Decimal("100")
        period = stripe_get(line, "period")
        period_start = from_unix(stripe_get(period, "start")) if period is not None else None
        period_end = from_unix(stripe_get(period, "end")) if period is not None else None
        invoice, _ = MembershipInvoice.objects.update_or_create(
            stripe_invoice_id=f"{invoice_id}::{item_id}",
            defaults={
                "membership": membership,
                "amount_paid": line_amount,
                "period_start": period_start,
                "period_end": period_end,
                **common,
            },
        )
        _refresh_membership_after_invoice(
            membership, invoice_id, period_start, period_end, amount_paid=line_amount
        )
        if first_invoice is None:
            first_invoice = invoice
    return first_invoice


def _refresh_membership_after_invoice(
    membership, invoice_id, period_start, period_end, *, amount_paid=None
):

    if period_end:
        membership.current_period_end = period_end
    if period_start:
        membership.current_period_start = period_start
    if membership.status in (MembershipStatus.PENDING, MembershipStatus.PAST_DUE):
        membership.status = MembershipStatus.ACTIVE
    membership.last_invoice_id = invoice_id
    membership.save(
        update_fields=[
            "current_period_start",
            "current_period_end",
            "status",
            "last_invoice_id",
            "updated_at",
        ]
    )
    record_membership_event(
        membership.person,
        MembershipTimelineEventType.PAYMENT_CONFIRMED,
        membership=membership,
        actor=None,
        context={
            "amount": str(amount_paid) if amount_paid is not None else "",
            "stripe_invoice_id": invoice_id,
        },
    )


@transaction.atomic
def mark_invoice_failed(stripe_invoice):

    subscription_id = stripe_get(stripe_invoice, "subscription")
    if not subscription_id:
        return None
    memberships = list(
        Membership.objects.filter(stripe_subscription_id=str(subscription_id))
    )
    if not memberships:
        return None

    invoice_id = stripe_invoice["id"]
    amount_due = Decimal(stripe_get(stripe_invoice, "amount_due", 0) or 0) / Decimal("100")

    for membership in memberships:
        if membership.status == MembershipStatus.EXEMPTED:
            continue
        membership.status = MembershipStatus.PAST_DUE
        membership.save(update_fields=["status", "updated_at"])
        MembershipInvoice.objects.update_or_create(
            stripe_invoice_id=invoice_id,
            defaults={
                "membership": membership,
                "amount_paid": Decimal("0"),
                "currency": stripe_get(stripe_invoice, "currency", payment_currency()) or payment_currency(),
                "status": "failed",
                "hosted_invoice_url": stripe_get(stripe_invoice, "hosted_invoice_url", "") or "",
                "paid_at": None,
                "description": (
                    f"Cobrança falhou — R$ {amount_due} — atualize o cartão para regularizar."
                )[:255],
            },
        )
        record_membership_event(
            membership.person,
            MembershipTimelineEventType.PAYMENT_FAILED,
            membership=membership,
            actor=None,
            context={"amount": str(amount_due), "stripe_invoice_id": invoice_id},
        )
        try:
            notify_payment_failed(membership, stripe_invoice=stripe_invoice)
        except Exception:
            logger.exception("mark_invoice_failed: erro ao enviar notificação (membership=%s).", membership.pk)
    return memberships[0]


@transaction.atomic
def mark_membership_canceled(stripe_subscription):
    memberships = list(
        Membership.objects.filter(stripe_subscription_id=stripe_subscription["id"])
    )
    if not memberships:
        return None
    canceled_at = from_unix(stripe_get(stripe_subscription, "canceled_at")) or timezone.now()
    for membership in memberships:
        membership.status = MembershipStatus.CANCELED
        membership.cancel_at_period_end = False
        membership.canceled_at = canceled_at
        membership.save(
            update_fields=["status", "cancel_at_period_end", "canceled_at", "updated_at"]
        )
    for membership in memberships:
        record_membership_event(
            membership.person,
            MembershipTimelineEventType.MEMBERSHIP_CANCELED,
            membership=membership,
            actor=None,
            actor_is_admin=False,
            context={
                "plan_name": membership.effective_display_name,
                "stripe_subscription_id": membership.stripe_subscription_id,
            },
        )
        recompute_family_discounts_for_person(membership.person)
    return memberships[0]


@transaction.atomic
def record_refund_from_charge(stripe_charge):
    payment_intent_id = stripe_get(stripe_charge, "payment_intent")
    amount_refunded = Decimal(stripe_get(stripe_charge, "amount_refunded", 0) or 0) / Decimal("100")

    order = None
    if payment_intent_id:
        order = RegistrationOrder.objects.filter(
            stripe_payment_intent_id=str(payment_intent_id)
        ).first()
    if order is not None:
        order.refunded_at = timezone.now()
        if amount_refunded >= (order.total or Decimal("0")):
            order.payment_status = PaymentStatus.REFUNDED
        if amount_refunded > Decimal("0"):
            append_order_refund_record(
                order,
                amount_refunded,
                source="stripe_charge",
                cumulative=True,
                save=False,
            )
        order.save(update_fields=["refunded_at", "payment_status", "notes", "updated_at"])

    invoice = None
    if payment_intent_id:
        invoice = MembershipInvoice.objects.filter(
            stripe_payment_intent_id=str(payment_intent_id)
        ).first()
    if invoice is not None:
        invoice.amount_refunded = amount_refunded
        invoice.refunded_at = timezone.now()
        invoice.save(update_fields=["amount_refunded", "refunded_at", "updated_at"])

    return {"order": order, "invoice": invoice}
