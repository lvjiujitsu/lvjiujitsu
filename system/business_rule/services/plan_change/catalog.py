from decimal import Decimal
from django.utils import timezone
from system.business_rule.models.membership import MembershipStatus
from system.business_rule.models.plan import PlanPrice
from system.business_rule.selectors.plan_eligibility import (
    build_eligibility_context_for_person,
    get_eligible_plan_prices,
    get_eligible_plans,
)
from system.business_rule.services.membership import get_membership_owner
from system.business_rule.utils.plan_commercial import COMMERCIAL_TIER_LABELS, resolve_commercial_tier
from system.business_rule.services.plan_change.calculation import calculate_plan_change
from system.business_rule.services.plan_change.locking import is_plan_change_locked
from system.business_rule.services.plan_change.primitives import PlanChangeError, CYCLE_INSTALLMENTS, STRIPE_RECURRING_GATEWAY_CODE, build_installment_label, catalog_id_for_plan, current_plan_reference
from system.business_rule.services.plan_change.queries import get_last_paid_order


def serialize_plan_with_proration(plan, proration, *, is_current=False):
    is_plan_price = isinstance(plan, PlanPrice)
    is_family_plan = False if is_plan_price else plan.is_family_plan
    is_loyalty_plan = False if is_plan_price else plan.is_loyalty_plan
    tier = resolve_commercial_tier(
        is_family_plan=is_family_plan, is_loyalty_plan=is_loyalty_plan
    )
    code = (
        f"{plan.tier.code}-{plan.gateway_code}-{plan.billing_cycle}"
        if is_plan_price
        else plan.code
    )
    return {
        "id": catalog_id_for_plan(plan),
        "code": code,
        "name": plan.display_name,
        "commercial_tier": tier,
        "commercial_tier_label": COMMERCIAL_TIER_LABELS.get(tier, tier),
        "price": str(plan.price),
        "monthly_reference_price": (
            str(plan.monthly_reference_price)
            if plan.monthly_reference_price is not None
            else ""
        ),
        "cycle": plan.get_billing_cycle_display(),
        "billing_cycle": plan.billing_cycle,
        "payment_method": plan.payment_method,
        "payment_method_label": plan.get_payment_method_display(),
        "is_family_plan": is_family_plan,
        "audience": plan.audience,
        "audience_label": (
            plan.tier.get_audience_display() if is_plan_price else plan.get_audience_display()
        ),
        "weekly_frequency": plan.weekly_frequency,
        "weekly_frequency_label": (
            plan.tier.get_weekly_frequency_display()
            if is_plan_price
            else plan.get_weekly_frequency_display()
        ),
        "installment_label": build_installment_label(plan),
        "installment_count": (
            CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
            if plan.payment_method == "credit_card"
            else 0
        ),
        "gateway_code": plan.gateway_code,
        "requires_checkout": plan.gateway_code == STRIPE_RECURRING_GATEWAY_CODE,
        "is_current": is_current,
        "proration": (
            {
                "cycles_covered": proration["cycles_covered"],
                "extension_months": proration["extension_months"],
                "new_period_end": proration["new_period_end"].isoformat(),
                "leftover_credit": str(proration["leftover_credit"]),
                "additional_charge": str(proration["additional_charge"]),
                "is_upgrade": proration["is_upgrade"],
                "is_extension": proration["is_extension"],
                "has_leftover": proration["has_leftover"],
            }
            if proration is not None
            else {
                "cycles_covered": 0,
                "extension_months": 0,
                "new_period_end": "",
                "leftover_credit": "0.00",
                "additional_charge": "0.00",
                "is_upgrade": False,
                "is_extension": False,
                "has_leftover": False,
            }
        ),
    }


def build_membership_summary(membership):
    if membership is None:
        return None
    last_order = get_last_paid_order(membership)
    amount_paid = (
        Decimal(last_order.total) if last_order and last_order.total
        else Decimal(membership.effective_full_price or 0)
    )
    period_start = membership.current_period_start
    period_end = membership.current_period_end
    cycle_days = max((period_end - period_start).days, 1) if period_start and period_end else 0
    now = timezone.now()
    days_used = max(0, min((now - period_start).days, cycle_days)) if period_start else 0
    days_remaining = max(0, cycle_days - days_used)

    if amount_paid > 0 and cycle_days > 0:
        daily = amount_paid / Decimal(cycle_days)
        consumed = (daily * Decimal(days_used)).quantize(Decimal("0.01"))
        available = (amount_paid - consumed).quantize(Decimal("0.01"))
    else:
        consumed = Decimal("0.00")
        available = Decimal("0.00")
    if available < 0:
        available = Decimal("0.00")

    return {
        "plan_name": membership.effective_display_name,
        "plan_cycle": membership.effective_billing_cycle_display,
        "amount_paid": str(amount_paid.quantize(Decimal("0.01"))),
        "amount_consumed": str(consumed),
        "available_credit": str(available),
        "cycle_days": cycle_days,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "period_end": period_end.isoformat() if period_end else "",
        "payment_provider": last_order.payment_provider if last_order else "",
        "refund_supported": bool(
            last_order
            and last_order.payment_provider in ("stripe", "asaas")
            and (last_order.stripe_payment_intent_id or last_order.asaas_payment_id)
        ),
    }


def build_plan_catalog(person, membership):
    if not membership or membership.status not in (
        MembershipStatus.ACTIVE,
        MembershipStatus.EXEMPTED,
    ):
        return []
    if is_plan_change_locked(membership):
        return []
    billing_owner = get_membership_owner(person) or person
    eligibility = build_eligibility_context_for_person(billing_owner)
    current_plan = current_plan_reference(membership)
    current_catalog_id = catalog_id_for_plan(current_plan) if current_plan is not None else None

    legacy_plans = (
        get_eligible_plans(eligibility)
        .filter(is_loyalty_plan=True)
        .exclude(pk=membership.plan_id)
    )
    plan_prices = get_eligible_plan_prices(eligibility).exclude(pk=membership.plan_price_id)

    catalog = []
    proration_cache = {}
    if current_plan is not None:
        catalog.append(serialize_plan_with_proration(current_plan, None, is_current=True))
    for plan in list(legacy_plans) + list(plan_prices):
        catalog_id = catalog_id_for_plan(plan)
        if catalog_id == current_catalog_id:
            continue
        if catalog_id not in proration_cache:
            try:
                proration_cache[catalog_id] = calculate_plan_change(membership, plan)
            except PlanChangeError:
                proration_cache[catalog_id] = None
        proration = proration_cache[catalog_id]
        if proration is None:
            continue
        catalog.append(serialize_plan_with_proration(plan, proration))
    return catalog


def build_plan_catalog_filters(catalog):
    frequencies = []
    seen_frequencies = set()
    cycles = []
    seen_cycles = set()
    methods = []
    seen_methods = set()
    for plan in catalog:
        freq = plan["weekly_frequency"]
        if freq not in seen_frequencies:
            seen_frequencies.add(freq)
            frequencies.append({"value": freq, "label": plan["weekly_frequency_label"]})
        cycle = plan["billing_cycle"]
        if cycle not in seen_cycles:
            seen_cycles.add(cycle)
            cycles.append({"value": cycle, "label": plan["cycle"]})
        method = plan["payment_method"]
        if method not in seen_methods:
            seen_methods.add(method)
            methods.append({"value": method, "label": plan["payment_method_label"]})
    frequencies.sort(key=lambda item: item["value"])
    return {
        "frequencies": frequencies,
        "cycles": cycles,
        "methods": methods,
    }
