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
    _from_unix,
    _sget,
    activate_membership_from_paid_order,
    activate_membership_from_session,
    extract_stripe_subscription_period,
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
            session = event["data"]["object"]
            reference = (session["client_reference_id"] if "client_reference_id" in session else None) or ""
            if reference.startswith("pre-registration:"):
                _handle_pre_registration_checkout_completed(session)
            else:
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


def _handle_pre_registration_checkout_completed(session):
    from system.models import PreRegistration, PreRegistrationStatus

    reference = (session["client_reference_id"] if "client_reference_id" in session else None) or ""
    parts = reference.split(":")
    try:
        pr_pk = int(parts[1]) if len(parts) >= 2 else None
    except (ValueError, TypeError):
        pr_pk = None

    if not pr_pk:
        logger.warning("Webhook Stripe: client_reference_id inválido: %s", reference)
        return

    pr = PreRegistration.objects.filter(pk=pr_pk).first()
    if pr is None:
        logger.warning("Webhook Stripe: PreRegistration %s não encontrada", pr_pk)
        return

    subscription_id = (session["subscription"] if "subscription" in session else None) or ""
    customer_id = (session["customer"] if "customer" in session else None) or ""
    snapshot = pr.form_snapshot or {}
    plan_payment = snapshot.get("plan_payment") or {}
    session_id = session["id"] if "id" in session else ""
    plan_payment["stripe_session_id"] = session_id
    if subscription_id:
        plan_payment["stripe_subscription_id"] = str(subscription_id)
    if customer_id:
        plan_payment["stripe_customer_id"] = str(customer_id)
    snapshot["plan_payment"] = plan_payment
    snapshot["plan_paid"] = True

    pr.form_snapshot = snapshot
    pr.status = PreRegistrationStatus.PAYMENT_CONFIRMED
    pr.save(update_fields=["form_snapshot", "status", "updated_at"])
    logger.info("Webhook Stripe: PreRegistration %s confirmada via checkout", pr_pk)


def _apply_stripe_plan_change_migration(order, session, *, stripe_subscription=None):
    from system.services.plan_change import apply_plan_change

    active = (
        Membership.objects.filter(
            person=order.person,
            status__in=(MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED),
        )
        .order_by("-created_at")
        .first()
    )
    if active is None:
        return None

    new_plan = order.plan_price_ref if order.plan_price_ref_id else order.plan
    apply_plan_change(order, active, new_plan)

    update_fields = []
    if "subscription" in session and session["subscription"]:
        active.stripe_subscription_id = str(session["subscription"])
        update_fields.append("stripe_subscription_id")
    if "customer" in session and session["customer"]:
        active.stripe_customer_id = str(session["customer"])
        update_fields.append("stripe_customer_id")
    if stripe_subscription is not None:
        current_period_start, current_period_end = extract_stripe_subscription_period(
            stripe_subscription
        )
        if current_period_start:
            active.current_period_start = current_period_start
            update_fields.append("current_period_start")
        if current_period_end:
            active.current_period_end = current_period_end
            update_fields.append("current_period_end")
    if update_fields:
        update_fields.append("updated_at")
        active.save(update_fields=update_fields)
    return active


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

        if order.is_plan_change and (order.plan_id or order.plan_price_ref_id):
            membership = _apply_stripe_plan_change_migration(
                order, session, stripe_subscription=stripe_subscription
            )
            return order, membership

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

    if order.is_plan_change and (order.plan_id or order.plan_price_ref_id):
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
            new_plan = order.plan_price_ref if order.plan_price_ref_id else order.plan
            apply_plan_change(order, active, new_plan)
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
