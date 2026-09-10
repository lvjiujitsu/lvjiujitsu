from django.utils import timezone
from django.utils.formats import date_format
from system.business_rule.services.plan_change.primitives import PLAN_CHANGE_LOCKED_STATUSES, STRIPE_RECURRING_GATEWAY_CODE, membership_period_end_date


def plan_requires_stripe_checkout(plan):
    return getattr(plan, "gateway_code", "") == STRIPE_RECURRING_GATEWAY_CODE


def is_plan_change_locked(membership):
    if (
        membership is None
        or membership.status not in PLAN_CHANGE_LOCKED_STATUSES
        or (membership.plan_id is None and membership.plan_price_id is None)
    ):
        return False
    if membership.plan_price_id is not None:
        gateway_code = membership.plan_price.gateway_code
    else:
        gateway_code = getattr(membership.plan, "gateway_code", "")
    is_stripe_recurring = bool(
        membership.stripe_subscription_id
        or gateway_code == STRIPE_RECURRING_GATEWAY_CODE
    )
    if not is_stripe_recurring:
        return False
    if membership.current_period_end is None:
        return True
    return membership.current_period_end > timezone.now()


def get_plan_change_lock(membership):
    if not is_plan_change_locked(membership):
        return {
            "is_locked": False,
            "available_on": None,
            "message": "",
        }

    available_on = membership_period_end_date(membership)
    if available_on:
        message = (
            "Troca e cancelamento liberados em "
            f"{date_format(available_on, 'SHORT_DATE_FORMAT')}, "
            "após a carência da assinatura recorrente."
        )
    else:
        message = (
            "Troca e cancelamento bloqueados durante a carência da assinatura recorrente. "
            "Fale com a academia para consultar a data de liberação."
        )
    return {
        "is_locked": True,
        "available_on": available_on,
        "message": message,
    }
