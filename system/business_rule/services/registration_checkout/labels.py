from system.business_rule.utils.plan_commercial import resolve_commercial_tier


SIZE_SORT_ORDER = {
    "A0": 10,
    "A1": 11,
    "A2": 12,
    "A3": 13,
    "A4": 14,
    "A5": 15,
    "A6": 16,
    "F1": 21,
    "F2": 22,
    "F3": 23,
    "F4": 24,
    "M0": 31,
    "M1": 32,
    "M2": 33,
    "M3": 34,
    "M4": 35,
}


COLOR_SORT_ORDER = {
    "Branca": 10,
    "Branco": 10,
    "Cinza": 20,
    "Amarelo": 30,
    "Amarela": 30,
    "Laranja": 40,
    "Verde": 50,
    "Azul": 60,
    "Roxa": 70,
    "Marrom": 80,
    "Preto": 90,
}


CYCLE_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}


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


def plan_charge_group_key(plan):
    tier = resolve_commercial_tier(
        is_family_plan=plan.is_family_plan, is_loyalty_plan=plan.is_loyalty_plan
    )
    return (plan.audience, tier, plan.weekly_frequency, plan.is_family_plan, plan.billing_cycle)


def build_installment_label_for_price(plan_price):
    if plan_price.payment_method != "credit_card":
        return ""
    n = CYCLE_INSTALLMENTS.get(plan_price.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan_price.monthly_reference_price:
        price_str = f"R$ {plan_price.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"


def build_variant_option_label(variant):
    parts = []
    if variant.color:
        parts.append(variant.color)
    if variant.size:
        parts.append(variant.size)
    if not parts:
        parts.append("Padrão")
    if variant.stock_quantity > 0:
        parts.append(f"{variant.stock_quantity} un.")
    else:
        parts.append("Esgotado")
    return " · ".join(parts)
