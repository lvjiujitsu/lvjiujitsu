from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from system.business_rule.models.membership import MembershipStatus
from system.business_rule.services.membership import MONTHS_BY_BILLING_CYCLE, add_months
from system.business_rule.services.plan_change.primitives import PlanChangeError, catalog_id_for_plan, current_plan_reference, quantize
from system.business_rule.services.plan_change.queries import get_membership_amount_paid


def calculate_plan_change(membership, new_plan):
    if membership.status not in (MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED):
        raise PlanChangeError("Somente assinaturas ativas podem trocar de plano.")
    if not membership.current_period_start or not membership.current_period_end:
        raise PlanChangeError("Assinatura sem período definido.")
    current_plan = current_plan_reference(membership)
    if current_plan is not None and catalog_id_for_plan(current_plan) == catalog_id_for_plan(new_plan):
        raise PlanChangeError("Plano selecionado é o mesmo que o atual.")

    now = timezone.now()
    period_start = membership.current_period_start
    period_end = membership.current_period_end

    cycle_days = (period_end - period_start).days
    if cycle_days <= 0:
        raise PlanChangeError("Ciclo de cobrança inválido.")

    days_used = max(0, min((now - period_start).days, cycle_days))
    days_remaining = cycle_days - days_used

    amount_paid = get_membership_amount_paid(membership)

    if amount_paid <= 0:
        amount_consumed = Decimal("0.00")
        available_credit = Decimal("0.00")
    else:
        daily_value = (amount_paid / Decimal(cycle_days)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        amount_consumed = quantize(daily_value * Decimal(days_used))
        available_credit = quantize(amount_paid - amount_consumed)
        if available_credit < 0:
            available_credit = Decimal("0.00")

    new_price = quantize(new_plan.price or Decimal("0"))

    if new_price <= 0:
        cycles_covered = 1
        leftover_credit = available_credit
        additional_charge = Decimal("0.00")
    elif available_credit >= new_price:
        cycles_covered = int(available_credit // new_price)
        leftover_credit = quantize(
            available_credit - (Decimal(cycles_covered) * new_price)
        )
        additional_charge = Decimal("0.00")
    else:
        cycles_covered = 1
        leftover_credit = Decimal("0.00")
        additional_charge = quantize(new_price - available_credit)

    extension_months = cycles_covered * MONTHS_BY_BILLING_CYCLE.get(
        new_plan.billing_cycle, 1
    )
    new_period_end = add_months(now, extension_months)

    is_upgrade = additional_charge > 0
    is_extension = not is_upgrade and cycles_covered >= 1
    has_leftover = leftover_credit > 0

    return {
        "current_plan": current_plan,
        "new_plan": new_plan,
        "cycle_days": cycle_days,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "amount_paid": amount_paid,
        "amount_consumed": amount_consumed,
        "available_credit": available_credit,
        "cycles_covered": cycles_covered,
        "extension_months": extension_months,
        "new_period_end": new_period_end,
        "leftover_credit": leftover_credit,
        "additional_charge": additional_charge,
        "is_upgrade": is_upgrade,
        "is_extension": is_extension,
        "has_leftover": has_leftover,
        "period_end": period_end,
        "now": now,
    }
