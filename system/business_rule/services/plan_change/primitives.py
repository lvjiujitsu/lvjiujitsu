from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from system.business_rule.models.membership import MembershipStatus
from system.business_rule.models.plan import PlanPrice
from system.business_rule.services.registration_checkout import (
    CATALOG_ID_PREFIX_PLAN_PRICE,
    CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
    build_catalog_plan_id,
)


def catalog_id_for_plan(plan_obj):
    if isinstance(plan_obj, PlanPrice):
        return build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, plan_obj.pk)
    return build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, plan_obj.pk)


def current_plan_reference(membership):
    if membership.plan_price_id is not None:
        return membership.plan_price
    return membership.plan


class PlanChangeError(Exception):
    pass


CYCLE_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}


STRIPE_RECURRING_GATEWAY_CODE = "stripe_card"


PLAN_CHANGE_LOCKED_STATUSES = (
    MembershipStatus.ACTIVE,
    MembershipStatus.EXEMPTED,
)


def quantize(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def membership_period_end_date(membership):
    period_end = getattr(membership, "current_period_end", None)
    if period_end is None:
        return None
    if timezone.is_aware(period_end):
        return timezone.localtime(period_end).date()
    return period_end.date()


def build_installment_label(plan):
    if plan.payment_method != "credit_card":
        return ""
    n = CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan.monthly_reference_price:
        price_str = f"R$ {plan.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"
