import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from system.models.registration_order import OrderKind, RegistrationOrder
from system.models.registration_order import PaymentProvider
from system.runtime_config import payment_currency
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


def _create_subscription_session(client, order, plan, customer_id, success_url, cancel_url):
    price_to_charge = order.total if order.total else plan.price
    if not price_to_charge or Decimal(str(price_to_charge)) <= Decimal("0"):
        raise StripeCheckoutError("Plano sem valor cobrável.")
    return client.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer=customer_id,
        line_items=[{
            "price_data": {
                "currency": payment_currency(),
                "unit_amount": _to_cents(price_to_charge),
                "recurring": {"interval": "month"},
                "product_data": {
                    "name": f"Mensalidade LV Jiu Jitsu — {plan.display_name}",
                },
            },
            "quantity": 1,
        }],
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


def create_billing_portal_session(membership, request):
    client = _get_client()
    if not membership.stripe_customer_id:
        raise StripeCheckoutError("Assinatura sem cliente Stripe vinculado.")

    return_url = request.build_absolute_uri(
        reverse("system:membership-update-card")
    ) + "?card_update=confirm"
    return client.billing_portal.Session.create(
        customer=membership.stripe_customer_id,
        return_url=return_url,
        flow_data={"type": "payment_method_update"},
    )


def get_membership_default_payment_method_id(membership):
    client = _get_client()
    try:
        subscription = client.Subscription.retrieve(membership.stripe_subscription_id)
        subscription_payment_method = _stripe_object_id(
            _stripe_value(subscription, "default_payment_method")
        )
        if subscription_payment_method:
            return subscription_payment_method

        customer = client.Customer.retrieve(membership.stripe_customer_id)
        invoice_settings = _stripe_value(customer, "invoice_settings") or {}
        return _stripe_object_id(
            _stripe_value(invoice_settings, "default_payment_method")
        )
    except stripe.error.StripeError as exc:
        logger.exception(
            "Falha ao consultar forma de pagamento Stripe da matrícula %s",
            membership.pk,
        )
        raise StripeCheckoutError(
            "Não foi possível validar a forma de pagamento na Stripe."
        ) from exc


def _stripe_object_id(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id") or ""
    return getattr(value, "id", "") or ""


def _stripe_value(container, key):
    try:
        return container[key]
    except (KeyError, TypeError):
        return getattr(container, key, None)


def create_subscription_session_for_plan_change(order, request):
    client = _get_client()
    plan = order.plan_price_ref if order.plan_price_ref_id else order.plan
    if plan is None:
        raise StripeCheckoutError("Pedido de troca de plano sem plano de destino.")

    success_url = request.build_absolute_uri(reverse("system:home")) + "?plan_migration=success"
    cancel_url = request.build_absolute_uri(reverse("system:home")) + "?plan_migration=canceled"
    customer_id = ensure_stripe_customer(order.person)

    session = _create_subscription_session(
        client, order, plan, customer_id, success_url, cancel_url
    )
    order.kind = OrderKind.SUBSCRIPTION
    order.stripe_session_id = session["id"]
    order.save(update_fields=["stripe_session_id", "kind", "updated_at"])
    return session


def _create_one_time_session(client, order, has_plan, customer_id, success_url, cancel_url):
    line_items = []
    items_subtotal = Decimal("0")

    if has_plan:
        line_items.append(
            {
                "price_data": {
                    "currency": payment_currency(),
                    "unit_amount": _to_cents(order.plan_price),
                    "product_data": {
                        "name": f"Plano: {order.plan.display_name}",
                    },
                },
                "quantity": 1,
            }
        )
        items_subtotal += Decimal(str(order.plan_price or "0"))

    for item in order.items.all():
        line_items.append(
            {
                "price_data": {
                    "currency": payment_currency(),
                    "unit_amount": _to_cents(item.unit_price),
                    "product_data": {"name": item.product_name},
                },
                "quantity": item.quantity,
            }
        )
        items_subtotal += Decimal(str(item.unit_price or "0")) * item.quantity

    order_total = Decimal(str(order.total or "0"))
    fee_amount = (order_total - items_subtotal).quantize(Decimal("0.01"))
    if fee_amount >= Decimal("0.01"):
        line_items.append(
            {
                "price_data": {
                    "currency": payment_currency(),
                    "unit_amount": _to_cents(fee_amount),
                    "product_data": {"name": "Taxa cartão de crédito"},
                },
                "quantity": 1,
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


def create_subscription_session_for_pre_registration(
    pre_registration, plans_by_id, selected_plans, *,
    final_total=None, coupon_info=None, billing_cycle_anchor=None,
):
    client = _get_client()

    if len(selected_plans) != 1:
        raise StripeCheckoutError(
            "Stripe Subscriptions suporta apenas um plano por sessão."
        )

    item = selected_plans[0]
    plan = plans_by_id.get(item["plan_id"])
    if plan is None:
        raise StripeCheckoutError("Plano selecionado não encontrado.")

    price_to_charge = final_total if final_total is not None else plan.price
    if not price_to_charge or Decimal(str(price_to_charge)) <= Decimal("0"):
        raise StripeCheckoutError("Plano sem valor cobrável.")

    snapshot = pre_registration.form_snapshot or {}
    profile_raw = snapshot.get("registration_profile") or pre_registration.registration_profile
    profile = profile_raw[0] if isinstance(profile_raw, list) else profile_raw
    prefix = "guardian" if profile == "guardian" else "holder"
    email_raw = snapshot.get(f"{prefix}_email") or pre_registration.holder_email or ""
    customer_email = (email_raw[0] if isinstance(email_raw, list) else email_raw) or None

    success_url = (
        settings.SITE_BASE_URL.rstrip("/")
        + reverse("system:payment-success")
        + f"?pre_registration_id={pre_registration.pk}&stage=plan&session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = settings.SITE_BASE_URL.rstrip("/") + reverse("system:payment-cancel")

    subscription_data = {
        "metadata": {
            "pre_registration_id": str(pre_registration.pk),
            "stage": "plan",
        },
    }
    if billing_cycle_anchor is not None:
        subscription_data["billing_cycle_anchor"] = int(billing_cycle_anchor)

    session = client.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": payment_currency(),
                "unit_amount": _to_cents(price_to_charge),
                "recurring": {"interval": "month"},
                "product_data": {
                    "name": f"Mensalidade LV Jiu Jitsu — {plan.display_name}",
                },
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=f"pre-registration:{pre_registration.pk}:plan",
        customer_email=customer_email,
        subscription_data=subscription_data,
        metadata={
            "pre_registration_id": str(pre_registration.pk),
            "stage": "plan",
        },
    )

    plan_payment = {
        "stripe_session_id": session["id"],
        "total": str(price_to_charge),
        "items": [
            {
                "label": item.get("label", ""),
                "plan_id": plan.pk,
                "plan_name": plan.display_name,
                "price": str(plan.price),
            }
        ],
    }
    if coupon_info:
        plan_payment.update(coupon_info)

    snapshot["plan_payment"] = plan_payment
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])

    return session


def merge_plan_into_existing_subscription(owner_membership, plan):
    client = _get_client()

    if not owner_membership or not owner_membership.stripe_subscription_id:
        raise StripeCheckoutError(
            "Titular não possui assinatura Stripe ativa para receber a cobrança fundida."
        )
    if not plan.stripe_price_id:
        raise StripeCheckoutError(
            f"Plano '{plan.display_name}' sem Stripe Price sincronizado."
        )

    subscription_item = client.SubscriptionItem.create(
        subscription=owner_membership.stripe_subscription_id,
        price=plan.stripe_price_id,
    )
    return {
        "stripe_subscription_id": owner_membership.stripe_subscription_id,
        "stripe_subscription_item_id": subscription_item["id"],
    }


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
