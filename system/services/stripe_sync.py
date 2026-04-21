import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.utils import timezone

from system.runtime_config import payment_currency


logger = logging.getLogger(__name__)


class StripeSyncError(Exception):
    pass


def _get_client():
    if not settings.STRIPE_SECRET_KEY:
        raise StripeSyncError("STRIPE_SECRET_KEY não configurada no .env")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _to_cents(value):
    return int((Decimal(value) * 100).quantize(Decimal("1")))


def sync_plan_to_stripe(plan):
    from system.models.plan import SubscriptionPlan

    client = _get_client()
    now = timezone.now()

    try:
        plan_price = Decimal(plan.price) if plan.price is not None else None
    except (TypeError, ValueError):
        plan_price = None
    if plan_price is None or plan_price <= 0:
        plan.stripe_sync_error = ""
        plan.stripe_synced_at = now
        SubscriptionPlan.objects.filter(pk=plan.pk).update(
            stripe_sync_error="",
            stripe_synced_at=now,
        )
        return plan

    try:
        product = _ensure_product(client, plan)
        price = _ensure_price(client, plan, product)
    except Exception as exc:
        logger.exception("Falha ao sincronizar plano %s com Stripe", plan.pk)
        SubscriptionPlan.objects.filter(pk=plan.pk).update(
            stripe_sync_error=str(exc)[:2000],
            stripe_synced_at=now,
        )
        raise StripeSyncError(str(exc)) from exc

    update_fields = {
        "stripe_product_id": product["id"],
        "stripe_price_id": price["id"],
        "stripe_archived_price_ids": plan.stripe_archived_price_ids,
        "stripe_sync_error": "",
        "stripe_synced_at": now,
    }
    SubscriptionPlan.objects.filter(pk=plan.pk).update(**update_fields)
    for field, value in update_fields.items():
        setattr(plan, field, value)
    return plan


def _ensure_product(client, plan):
    if plan.stripe_product_id:
        product = client.Product.modify(
            plan.stripe_product_id,
            name=plan.display_name,
            description=plan.description or None,
            active=plan.is_active,
            metadata={"plan_id": str(plan.pk), "plan_code": plan.code},
        )
        return product
    return client.Product.create(
        name=plan.display_name,
        description=plan.description or None,
        active=plan.is_active,
        metadata={"plan_id": str(plan.pk), "plan_code": plan.code},
    )


def _price_matches(price_obj, plan):
    interval = plan.stripe_interval
    if interval is None:
        return False
    unit_amount = _to_cents(plan.price)
    recurring = price_obj["recurring"] if "recurring" in price_obj else None
    if not recurring:
        return False
    return (
        price_obj["unit_amount"] == unit_amount
        and price_obj["currency"] == payment_currency()
        and recurring["interval"] == interval[0]
        and recurring["interval_count"] == interval[1]
        and price_obj["active"]
    )


def _ensure_price(client, plan, product):
    interval = plan.stripe_interval
    if interval is None:
        raise StripeSyncError(
            f"Ciclo de cobrança {plan.billing_cycle} sem mapeamento Stripe"
        )

    if plan.stripe_price_id:
        try:
            current = client.Price.retrieve(plan.stripe_price_id)
        except Exception:
            current = None
        if current is not None and _price_matches(current, plan):
            return current
        if current is not None and current["active"]:
            client.Price.modify(plan.stripe_price_id, active=False)
            archived = list(plan.stripe_archived_price_ids or [])
            if plan.stripe_price_id and plan.stripe_price_id not in archived:
                archived.append(plan.stripe_price_id)
            plan.stripe_archived_price_ids = archived

    interval_name, interval_count = interval
    new_price = client.Price.create(
        product=product["id"],
        currency=payment_currency(),
        unit_amount=_to_cents(plan.price),
        recurring={"interval": interval_name, "interval_count": interval_count},
        metadata={"plan_id": str(plan.pk), "plan_code": plan.code},
    )
    return new_price


def ensure_stripe_customer(person):
    client = _get_client()
    if person.stripe_customer_id:
        return person.stripe_customer_id
    customer = client.Customer.create(
        name=person.full_name,
        email=person.email or None,
        phone=person.phone or None,
        metadata={"person_id": str(person.pk), "cpf": person.cpf},
    )
    from system.models.person import Person

    Person.objects.filter(pk=person.pk).update(stripe_customer_id=customer["id"])
    person.stripe_customer_id = customer["id"]
    return customer["id"]
