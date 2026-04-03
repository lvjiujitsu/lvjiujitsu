import json
import logging
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import (
    AuditLog,
    LocalSubscription,
    MonthlyInvoice,
    StripeSubscriptionLink,
    WebhookProcessing,
)
from system.services.finance import mark_invoice_overdue, mark_invoice_paid, sync_subscription_status
from system.services.payments.checkout import expire_checkout_request, record_checkout_completion
from system.services.payments.gateway import construct_event, normalize_stripe_payload
from system.services.payments.mirror import process_event_payload, sync_invoice_payload, sync_subscription_payload
from system.services.reports.audit import record_audit_log

logger = logging.getLogger(__name__)


def verify_stripe_event(*, payload, signature):
    if settings.STRIPE_WEBHOOK_SECRET:
        return normalize_stripe_payload(construct_event(payload=payload, signature=signature))
    return json.loads(payload.decode("utf-8"))


@transaction.atomic
def process_stripe_webhook(*, payload, signature):
    event = verify_stripe_event(payload=payload, signature=signature)
    event_id = event["id"]
    processing, created = WebhookProcessing.objects.get_or_create(
        stripe_event_id=event_id,
        defaults={
            "event_type": event["type"],
            "payload": event,
            "signature_verified": bool(settings.STRIPE_WEBHOOK_SECRET),
            "livemode": bool(event.get("livemode", False)),
        },
    )
    if not created and processing.status == WebhookProcessing.STATUS_PROCESSED:
        return processing, True
    processing.event_type = event["type"]
    processing.payload = event
    processing.processing_attempts += 1
    processing.signature_verified = bool(settings.STRIPE_WEBHOOK_SECRET)
    processing.livemode = bool(event.get("livemode", False))
    processing.save(update_fields=["event_type", "payload", "processing_attempts", "signature_verified", "livemode", "updated_at"])
    try:
        process_event_payload(event)
        _dispatch_event(event)
    except Exception as exc:
        processing.status = WebhookProcessing.STATUS_FAILED
        processing.failure_message = str(exc)
        processing.processed_at = timezone.now()
        processing.save(update_fields=["status", "failure_message", "processed_at", "updated_at"])
        record_audit_log(
            category=AuditLog.CATEGORY_PAYMENTS,
            action="stripe_webhook_failed",
            target=processing,
            status=AuditLog.STATUS_FAILURE,
            metadata={"event_id": event_id, "event_type": event["type"], "error": str(exc)},
        )
        logger.exception("stripe_webhook_failed", extra={"event_id": event_id, "event_type": event["type"]})
        raise
    processing.status = WebhookProcessing.STATUS_PROCESSED
    processing.processed_at = timezone.now()
    processing.failure_message = ""
    processing.save(update_fields=["status", "processed_at", "failure_message", "updated_at"])
    record_audit_log(
        category=AuditLog.CATEGORY_PAYMENTS,
        action="stripe_webhook_processed",
        target=processing,
        metadata={"event_id": event_id, "event_type": event["type"], "duplicate": not created},
    )
    logger.info("stripe_webhook_processed", extra={"event_id": event_id, "event_type": event["type"], "duplicate": not created})
    return processing, False


def _dispatch_event(event):
    event_type = event["type"]
    payload = event["data"]["object"]
    handlers = {
        "checkout.session.completed": _handle_checkout_session_completed,
        "checkout.session.expired": _handle_checkout_session_expired,
        "invoice.paid": _handle_invoice_paid,
        "invoice.payment_failed": _handle_invoice_payment_failed,
        "customer.subscription.created": _handle_subscription_updated,
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
    }
    handler = handlers.get(event_type)
    if handler is None:
        return
    handler(payload)


def _handle_checkout_session_completed(session_payload):
    record_checkout_completion(session_payload)


def _handle_checkout_session_expired(session_payload):
    expire_checkout_request(session_payload)


def _handle_invoice_paid(invoice_payload):
    sync_invoice_payload(invoice_payload)
    _mark_link_as_active(invoice_payload.get("subscription"))
    invoice = _upsert_local_invoice(invoice_payload)
    mark_invoice_paid(invoice, notes="Pagamento confirmado via webhook Stripe.")


def _handle_invoice_payment_failed(invoice_payload):
    sync_invoice_payload(invoice_payload)
    _mark_link_as_past_due(invoice_payload.get("subscription"))
    invoice = _upsert_local_invoice(invoice_payload)
    mark_invoice_overdue(invoice, notes="Falha de pagamento confirmada via webhook Stripe.")


def _handle_subscription_updated(subscription_payload):
    sync_subscription_payload(subscription_payload)
    link = _resolve_subscription_link(subscription_payload["id"])
    pause_collection = subscription_payload.get("pause_collection") or {}
    link.stripe_status = _map_subscription_status(subscription_payload, pause_collection)
    link.pause_collection_behavior = pause_collection.get("behavior", "")
    link.pause_collection_resumes_at = _timestamp_to_datetime(pause_collection.get("resumes_at"))
    link.current_period_start = _timestamp_to_datetime(subscription_payload.get("current_period_start"))
    link.current_period_end = _timestamp_to_datetime(subscription_payload.get("current_period_end"))
    link.latest_payload = subscription_payload
    link.livemode = bool(subscription_payload.get("livemode", False))
    link.save(
        update_fields=[
            "stripe_status",
            "pause_collection_behavior",
            "pause_collection_resumes_at",
            "current_period_start",
            "current_period_end",
            "latest_payload",
            "livemode",
            "updated_at",
        ]
    )
    sync_subscription_status(link.local_subscription)


def _handle_subscription_deleted(subscription_payload):
    sync_subscription_payload(subscription_payload)
    link = _resolve_subscription_link(subscription_payload["id"])
    link.stripe_status = StripeSubscriptionLink.STATUS_CANCELLED
    link.latest_payload = subscription_payload
    link.livemode = bool(subscription_payload.get("livemode", False))
    link.save(update_fields=["stripe_status", "latest_payload", "livemode", "updated_at"])
    local_subscription = link.local_subscription
    local_subscription.status = LocalSubscription.STATUS_CANCELLED
    local_subscription.save(update_fields=["status", "updated_at"])
    sync_subscription_status(local_subscription)


def _resolve_subscription_link(stripe_subscription_id):
    link = StripeSubscriptionLink.objects.select_related("local_subscription").filter(
        stripe_subscription_id=stripe_subscription_id
    ).first()
    if link is None:
        raise ValidationError("Assinatura Stripe sem vinculo local.")
    return link


def _mark_link_as_active(stripe_subscription_id):
    if not stripe_subscription_id:
        return None
    link = _resolve_subscription_link(stripe_subscription_id)
    link.stripe_status = StripeSubscriptionLink.STATUS_ACTIVE
    link.save(update_fields=["stripe_status", "updated_at"])
    return link


def _mark_link_as_past_due(stripe_subscription_id):
    if not stripe_subscription_id:
        return None
    link = _resolve_subscription_link(stripe_subscription_id)
    link.stripe_status = StripeSubscriptionLink.STATUS_PAST_DUE
    link.save(update_fields=["stripe_status", "updated_at"])
    return link


def _upsert_local_invoice(invoice_payload):
    link = _resolve_subscription_link(invoice_payload["subscription"])
    reference_month = _resolve_reference_month(invoice_payload)
    amount_total = _to_decimal(invoice_payload.get("total"))
    amount_subtotal = _to_decimal(invoice_payload.get("subtotal"))
    amount_discount = max(amount_subtotal - amount_total, Decimal("0.00"))
    invoice, _ = MonthlyInvoice.objects.get_or_create(
        subscription=link.local_subscription,
        reference_month=reference_month,
        defaults={
            "due_date": _resolve_due_date(invoice_payload),
            "amount_gross": amount_subtotal or amount_total,
            "amount_discount": amount_discount,
            "amount_net": amount_total,
            "stripe_invoice_id": invoice_payload["id"],
        },
    )
    invoice.due_date = _resolve_due_date(invoice_payload)
    invoice.amount_gross = amount_subtotal or amount_total
    invoice.amount_discount = amount_discount
    invoice.amount_net = amount_total
    invoice.stripe_invoice_id = invoice_payload["id"]
    invoice.notes = f"Sincronizada a partir da invoice Stripe {invoice_payload['id']}."
    invoice.full_clean()
    invoice.save()
    return invoice


def _resolve_reference_month(invoice_payload):
    period_start = invoice_payload.get("period_start") or invoice_payload.get("created")
    reference = _timestamp_to_datetime(period_start) or timezone.now()
    return reference.date().replace(day=1)


def _resolve_due_date(invoice_payload):
    due_timestamp = invoice_payload.get("due_date") or invoice_payload.get("created")
    resolved = _timestamp_to_datetime(due_timestamp) or timezone.now()
    return resolved.date()


def _timestamp_to_datetime(value):
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.get_current_timezone())


def _to_decimal(value):
    if value in (None, ""):
        return Decimal("0.00")
    return (Decimal(value) / Decimal("100")).quantize(Decimal("0.01"))


def _map_subscription_status(subscription_payload, pause_collection):
    if pause_collection:
        return StripeSubscriptionLink.STATUS_PAUSED_COLLECTION
    status = subscription_payload.get("status")
    mapping = {
        "active": StripeSubscriptionLink.STATUS_ACTIVE,
        "past_due": StripeSubscriptionLink.STATUS_PAST_DUE,
        "canceled": StripeSubscriptionLink.STATUS_CANCELLED,
        "unpaid": StripeSubscriptionLink.STATUS_PAST_DUE,
        "incomplete": StripeSubscriptionLink.STATUS_PENDING,
    }
    return mapping.get(status, StripeSubscriptionLink.STATUS_UNKNOWN)
