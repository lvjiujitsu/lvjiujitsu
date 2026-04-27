import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.models.membership import Membership, MembershipStatus
from system.models.registration_order import (
    PaymentStatus,
    RegistrationOrder,
    StripeWebhookEvent,
)
from system.services.membership import (
    activate_membership_from_paid_order,
    activate_membership_from_session,
    mark_invoice_failed,
    mark_membership_canceled,
    record_invoice_from_stripe,
    record_refund_from_charge,
    upsert_membership_from_stripe_subscription,
)
from system.services.financial_transactions import apply_order_financials
from system.services.registration_checkout import apply_order_variant_stock
from system.services.stripe_checkout import resolve_order_from_session


logger = logging.getLogger(__name__)


def _get_client():
    if settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


@transaction.atomic
def process_stripe_event(event):
    event_id = event["id"]
    event_type = event["type"]

    existing = (
        StripeWebhookEvent.objects.select_for_update()
        .filter(event_id=event_id)
        .first()
    )
    if existing is not None:
        return {
            "order": existing.order,
            "membership": existing.membership,
            "duplicate": True,
        }

    order = None
    membership = None

    try:
        if event_type == "checkout.session.completed":
            order, membership = _handle_checkout_session_completed(event)
        elif event_type == "checkout.session.expired":
            order = _handle_checkout_session_expired(event)
        elif event_type == "payment_intent.payment_failed":
            order = _handle_payment_intent_failed(event)
        elif event_type == "invoice.paid":
            invoice = record_invoice_from_stripe(event["data"]["object"])
            if invoice is not None:
                membership = invoice.membership
        elif event_type == "invoice.payment_failed":
            membership = mark_invoice_failed(event["data"]["object"])
        elif event_type == "customer.subscription.updated":
            membership = upsert_membership_from_stripe_subscription(
                event["data"]["object"]
            )
        elif event_type == "customer.subscription.deleted":
            membership = mark_membership_canceled(event["data"]["object"])
        elif event_type in ("charge.refunded", "charge.refund.updated"):
            result = record_refund_from_charge(event["data"]["object"])
            order = result["order"]
            if result["invoice"] is not None:
                membership = result["invoice"].membership
    except Exception:
        logger.exception(
            "Falha ao processar evento Stripe %s (%s)", event_id, event_type
        )
        raise

    StripeWebhookEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
        order=order,
        membership=membership,
        payload={"id": event_id, "type": event_type},
    )
    return {"order": order, "membership": membership, "duplicate": False}


def _handle_checkout_session_completed(event):
    session = event["data"]["object"]
    order = resolve_order_from_session(session)
    if order is None:
        return None, None

    mode = session["mode"] if "mode" in session else "payment"

    if mode == "subscription":
        was_paid = order.payment_status in (PaymentStatus.PAID, PaymentStatus.EXEMPTED)
        stripe_subscription = None
        subscription_id = session["subscription"] if "subscription" in session else None
        if subscription_id:
            try:
                client = _get_client()
                stripe_subscription = client.Subscription.retrieve(subscription_id)
            except Exception:
                logger.exception(
                    "Falha ao recuperar Subscription %s do Stripe", subscription_id
                )
        order.payment_status = PaymentStatus.PAID
        order.paid_at = timezone.now()
        order.stripe_session_id = session["id"]
        if subscription_id:
            order.stripe_subscription_id = str(subscription_id)
        order.save(
            update_fields=[
                "payment_status",
                "paid_at",
                "stripe_session_id",
                "stripe_subscription_id",
                "updated_at",
            ]
        )
        if not was_paid:
            apply_order_variant_stock(order)
        membership = activate_membership_from_session(
            order, session, stripe_subscription=stripe_subscription
        )
        return order, membership

    was_paid = order.payment_status in (PaymentStatus.PAID, PaymentStatus.EXEMPTED)
    order.payment_status = PaymentStatus.PAID
    order.paid_at = timezone.now()
    order.stripe_session_id = session["id"]
    if "payment_intent" in session and session["payment_intent"]:
        order.stripe_payment_intent_id = str(session["payment_intent"])
    order.save(
        update_fields=[
            "payment_status",
            "paid_at",
            "stripe_session_id",
            "stripe_payment_intent_id",
            "updated_at",
        ]
    )
    if not was_paid:
        apply_order_variant_stock(order)
    apply_order_financials(
        order,
        financial_transaction_id=order.stripe_payment_intent_id or session["id"],
        mark_available=True,
    )

    if order.is_plan_change and order.plan_id:
        from system.services.plan_change import apply_plan_change

        active = (
            Membership.objects.filter(
                person=order.person,
                status__in=(MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED),
            )
            .order_by("-created_at")
            .first()
        )
        if active:
            apply_plan_change(order, active, order.plan)
            return order, active

    membership = activate_membership_from_paid_order(
        order,
        notes="Pagamento confirmado via Stripe.",
    )
    return order, membership


def _handle_checkout_session_expired(event):
    session = event["data"]["object"]
    order = resolve_order_from_session(session)
    if order is None:
        return None
    if order.payment_status in (PaymentStatus.PAID, PaymentStatus.EXEMPTED):
        return order
    order.payment_status = PaymentStatus.CANCELED
    order.save(update_fields=["payment_status", "updated_at"])
    return order


def _handle_payment_intent_failed(event):
    pi = event["data"]["object"]
    pi_id = pi["id"] if "id" in pi else None
    if not pi_id:
        return None
    order = RegistrationOrder.objects.filter(
        stripe_payment_intent_id=str(pi_id)
    ).first()
    if order is None:
        return None
    if order.payment_status in (PaymentStatus.PAID, PaymentStatus.EXEMPTED):
        return order
    order.payment_status = PaymentStatus.FAILED
    order.save(update_fields=["payment_status", "updated_at"])
    return order
