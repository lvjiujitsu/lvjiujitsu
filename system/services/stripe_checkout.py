import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.urls import reverse

from system.models.registration_order import OrderKind, RegistrationOrder
from system.models.registration_order import PaymentProvider
from system.services.financial_transactions import apply_order_financials
from system.services.stripe_sync import ensure_stripe_customer


logger = logging.getLogger(__name__)


class StripeCheckoutError(Exception):
    pass


def _get_client():
    if not settings.STRIPE_SECRET_KEY:
        raise StripeCheckoutError("STRIPE_SECRET_KEY não configurada no .env")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _to_cents(value):
    return int((Decimal(value) * 100).quantize(Decimal("1")))


def verify_webhook_event(payload, sig_header):
    client = _get_client()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise StripeCheckoutError("STRIPE_WEBHOOK_SECRET não configurado no .env")
    return client.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )


def create_checkout_session_for_order(order, request):
    client = _get_client()
    has_plan = bool(order.plan_id and order.plan and order.plan.price and order.plan.price > 0)
    has_items = order.items.exists()

    if not has_plan and not has_items:
        raise StripeCheckoutError("Pedido sem itens cobráveis")

    success_url = request.build_absolute_uri(
        reverse("system:payment-success")
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("system:payment-cancel"))

    customer_id = ensure_stripe_customer(order.person)

    session = _create_one_time_session(
        client, order, has_plan, customer_id, success_url, cancel_url
    )
    order.kind = OrderKind.ONE_TIME

    order.stripe_session_id = session["id"]
    order.save(update_fields=["stripe_session_id", "kind", "updated_at"])
    apply_order_financials(
        order,
        payment_provider=PaymentProvider.STRIPE,
        financial_transaction_id=session["id"],
    )
    return session


def _create_subscription_session(client, order, customer_id, success_url, cancel_url):
    plan = order.plan
    if not plan.stripe_price_id:
        raise StripeCheckoutError(
            f"Plano '{plan.display_name}' sem Stripe Price sincronizado. "
            "Salve o plano para disparar a sincronização."
        )
    return client.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer=customer_id,
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(order.pk),
        metadata={
            "registration_order_id": str(order.pk),
            "person_id": str(order.person_id),
            "plan_id": str(plan.pk),
        },
        subscription_data={
            "metadata": {
                "registration_order_id": str(order.pk),
                "person_id": str(order.person_id),
                "plan_id": str(plan.pk),
            },
        },
    )


def _create_one_time_session(client, order, has_plan, customer_id, success_url, cancel_url):
    line_items = []
    if has_plan:
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
    return client.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        customer=customer_id,
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(order.pk),
        metadata={
            "registration_order_id": str(order.pk),
            "person_id": str(order.person_id),
        },
        payment_intent_data={
            "metadata": {
                "registration_order_id": str(order.pk),
                "person_id": str(order.person_id),
            },
        },
    )


def resolve_order_from_session(session):
    metadata = session["metadata"] if "metadata" in session else None
    order_id = None
    if metadata and "registration_order_id" in metadata:
        order_id = metadata["registration_order_id"]
    if not order_id and "client_reference_id" in session:
        order_id = session["client_reference_id"]
    if not order_id:
        return None
    try:
        return RegistrationOrder.objects.select_related("plan", "person").get(
            pk=int(order_id)
        )
    except (RegistrationOrder.DoesNotExist, ValueError, TypeError):
        return None
