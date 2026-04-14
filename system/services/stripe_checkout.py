from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from system.models.registration_order import (
    PaymentStatus,
    RegistrationOrder,
    StripeWebhookEvent,
)


class StripeCheckoutError(Exception):
    pass


def _get_client():
    if not settings.STRIPE_SECRET_KEY:
        raise StripeCheckoutError("STRIPE_SECRET_KEY não configurada no .env")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _to_cents(value):
    return int((Decimal(value) * 100).quantize(Decimal("1")))


def _build_line_items(order):
    line_items = []
    if order.plan and order.plan_price and order.plan_price > 0:
        line_items.append(
            {
                "price_data": {
                    "currency": "brl",
                    "unit_amount": _to_cents(order.plan_price),
                    "product_data": {
                        "name": f"Plano: {order.plan.display_name}",
                    },
                },
                "quantity": 1,
            }
        )
    for item in order.items.all():
        line_items.append(
            {
                "price_data": {
                    "currency": "brl",
                    "unit_amount": _to_cents(item.unit_price),
                    "product_data": {"name": item.product_name},
                },
                "quantity": item.quantity,
            }
        )
    return line_items


def create_checkout_session_for_order(order, request):
    client = _get_client()
    line_items = _build_line_items(order)
    if not line_items:
        raise StripeCheckoutError("Pedido sem itens cobráveis")

    success_url = request.build_absolute_uri(
        reverse("system:payment-success")
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("system:payment-cancel"))

    session = client.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(order.pk),
        metadata={"registration_order_id": str(order.pk)},
        customer_email=getattr(order.person, "email", None) or None,
    )

    order.stripe_session_id = session["id"]
    order.save(update_fields=["stripe_session_id", "updated_at"])
    return session


def verify_webhook_event(payload, sig_header):
    client = _get_client()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise StripeCheckoutError("STRIPE_WEBHOOK_SECRET não configurado no .env")
    return client.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )


def _resolve_order_from_session(session):
    metadata = session["metadata"] if "metadata" in session else None
    order_id = None
    if metadata and "registration_order_id" in metadata:
        order_id = metadata["registration_order_id"]
    if not order_id and "client_reference_id" in session:
        order_id = session["client_reference_id"]
    if not order_id:
        return None
    try:
        return RegistrationOrder.objects.get(pk=int(order_id))
    except (RegistrationOrder.DoesNotExist, ValueError, TypeError):
        return None


@transaction.atomic
def process_stripe_event(event):
    event_id = event["id"]
    event_type = event["type"]

    existing = StripeWebhookEvent.objects.select_for_update().filter(
        event_id=event_id
    ).first()
    if existing is not None:
        return {"order": existing.order, "duplicate": True}

    order = None
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        order = _mark_order_paid_from_session(session)
    elif event_type == "checkout.session.expired":
        session = event["data"]["object"]
        order = _mark_order_canceled_from_session(session)
    elif event_type == "payment_intent.payment_failed":
        pi = event["data"]["object"]
        order = _mark_order_failed_from_payment_intent(pi)

    StripeWebhookEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
        order=order,
        payload={"id": event_id, "type": event_type},
    )
    return {"order": order, "duplicate": False}


def _mark_order_paid_from_session(session):
    order = _resolve_order_from_session(session)
    if order is None:
        return None
    order.payment_status = PaymentStatus.PAID
    order.stripe_session_id = session["id"]
    if "payment_intent" in session and session["payment_intent"]:
        order.stripe_payment_intent_id = str(session["payment_intent"])
    order.paid_at = timezone.now()
    order.save(
        update_fields=[
            "payment_status",
            "stripe_session_id",
            "stripe_payment_intent_id",
            "paid_at",
            "updated_at",
        ]
    )
    return order


def _mark_order_canceled_from_session(session):
    order = _resolve_order_from_session(session)
    if order is None or order.payment_status == PaymentStatus.PAID:
        return order
    order.payment_status = PaymentStatus.CANCELED
    order.save(update_fields=["payment_status", "updated_at"])
    return order


def _mark_order_failed_from_payment_intent(payment_intent):
    pi_id = payment_intent["id"] if "id" in payment_intent else None
    if not pi_id:
        return None
    order = RegistrationOrder.objects.filter(
        stripe_payment_intent_id=pi_id
    ).first()
    if order is None or order.payment_status == PaymentStatus.PAID:
        return order
    order.payment_status = PaymentStatus.FAILED
    order.save(update_fields=["payment_status", "updated_at"])
    return order
