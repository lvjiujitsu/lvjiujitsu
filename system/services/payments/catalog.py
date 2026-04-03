from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import StripePlanPriceMap
from system.services.payments.gateway import normalize_stripe_payload


@transaction.atomic
def upsert_price_map_from_stripe_data(
    *,
    plan,
    price_payload,
    is_current=False,
    is_legacy=False,
    supports_pause_collection=True,
    notes="",
):
    price_payload = normalize_stripe_payload(price_payload)
    recurring_data = price_payload.get("recurring") or {}
    if not recurring_data:
        raise ValidationError("Somente Prices recorrentes da Stripe podem ser vinculados a planos locais.")

    stripe_price_id = price_payload.get("id")
    if not stripe_price_id:
        raise ValidationError("Price Stripe sem identificador.")

    resolved_today = timezone.localdate()
    if is_current:
        _retire_conflicting_current_maps(plan=plan, keep_price_id=stripe_price_id, retired_on=resolved_today)

    product_id, product_name = _resolve_product_snapshot(price_payload)
    price_map = StripePlanPriceMap.objects.filter(stripe_price_id=stripe_price_id).first()
    created = price_map is None
    if created:
        price_map = StripePlanPriceMap(
            plan=plan,
            stripe_price_id=stripe_price_id,
            valid_from=resolved_today,
        )

    price_map.plan = plan
    price_map.stripe_product_id = product_id
    price_map.product_name = product_name
    price_map.lookup_key = price_payload.get("lookup_key", "") or ""
    price_map.currency = (price_payload.get("currency") or "brl").lower()
    price_map.amount = _resolve_decimal_amount(price_payload)
    price_map.recurring_interval = recurring_data.get("interval", "") or ""
    price_map.recurring_interval_count = int(recurring_data.get("interval_count") or 1)
    price_map.livemode = bool(price_payload.get("livemode", False))
    price_map.supports_pause_collection = supports_pause_collection
    price_map.is_current = is_current
    price_map.is_legacy = is_legacy
    price_map.is_active = bool(price_payload.get("active", True)) and not is_legacy
    price_map.notes = notes or price_map.notes
    if is_current:
        price_map.valid_until = None
    elif is_legacy and not price_map.valid_until:
        price_map.valid_until = resolved_today

    price_map.full_clean()
    price_map.save()
    return price_map, created


def _retire_conflicting_current_maps(*, plan, keep_price_id, retired_on):
    StripePlanPriceMap.objects.filter(plan=plan, is_current=True).exclude(stripe_price_id=keep_price_id).update(
        is_current=False,
        is_active=False,
        is_legacy=True,
        valid_until=retired_on,
        updated_at=timezone.now(),
    )


def _resolve_product_snapshot(price_payload):
    product_payload = price_payload.get("product")
    if isinstance(product_payload, dict):
        return product_payload.get("id", ""), product_payload.get("name", "") or ""
    return product_payload or "", ""


def _resolve_decimal_amount(price_payload):
    raw_amount = price_payload.get("unit_amount_decimal")
    if raw_amount in (None, ""):
        raw_amount = price_payload.get("unit_amount")
    if raw_amount in (None, ""):
        raise ValidationError("Price Stripe sem valor monetario.")
    return (Decimal(str(raw_amount)) / Decimal("100")).quantize(Decimal("0.01"))
