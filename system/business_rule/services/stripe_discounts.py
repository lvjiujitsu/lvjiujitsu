import logging
from decimal import Decimal

import stripe
from django.conf import settings

from system.business_rule.services.membership_resolution import resolve_effective_tier


logger = logging.getLogger(__name__)


class StripeDiscountError(Exception):
    pass


def get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise StripeDiscountError("STRIPE_SECRET_KEY não configurada no .env")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _family_coupon_id(percent_off):
    percent = Decimal(str(percent_off)) * Decimal("10000")
    return f"family-discount-{int(percent)}"


def _ensure_family_coupon(client, percent_off):
    coupon_id = _family_coupon_id(percent_off)
    try:
        return client.Coupon.retrieve(coupon_id)
    except Exception:
        return client.Coupon.create(
            id=coupon_id,
            percent_off=float(Decimal(str(percent_off)) * 100),
            duration="forever",
        )


def apply_family_discount(membership):
    if not membership.stripe_subscription_id:
        return None
    tier = resolve_effective_tier(membership)
    if tier is None:
        raise StripeDiscountError("Membership sem tier associado não tem desconto família aplicável.")
    client = get_stripe_client()
    percent_off = tier.family_discount_percentage
    if not percent_off:
        return None
    coupon = _ensure_family_coupon(client, percent_off)
    return client.Subscription.modify(
        membership.stripe_subscription_id,
        discounts=[{"coupon": coupon["id"]}],
    )


def remove_family_discount(membership):
    if not membership.stripe_subscription_id:
        return None
    client = get_stripe_client()
    return client.Subscription.delete_discount(membership.stripe_subscription_id)
