from decimal import Decimal
from system.business_rule.models.plan import PlanPaymentMethod, PlanPrice, SubscriptionPlan
from system.business_rule.utils.plan_commercial import COMMERCIAL_TIER_LABELS, resolve_commercial_tier
from system.business_rule.services.registration_checkout.catalog_ids import CATALOG_ID_PREFIX_PLAN_PRICE, CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, build_catalog_plan_id
from system.business_rule.services.registration_checkout.labels import CYCLE_INSTALLMENTS, build_installment_label, build_installment_label_for_price, plan_charge_group_key


def get_plan_catalog_payload(*, include_plan_prices=False):
    payload = []
    payload.extend(_build_legacy_plan_catalog_payload(prefixed=include_plan_prices))
    if include_plan_prices:
        payload.extend(_build_plan_price_catalog_payload())
    return payload


def get_public_registration_plan_catalog_payload():
    return _build_plan_price_catalog_payload()


def _build_legacy_plan_catalog_payload(*, prefixed=False):
    plans = list(
        SubscriptionPlan.objects.filter(is_active=True)
        .exclude(requires_special_authorization=True)
        .order_by("display_order", "price")
    )
    groups = {}
    for plan in plans:
        slot = groups.setdefault(plan_charge_group_key(plan), {})
        slot[plan.payment_method] = plan
    cent = Decimal("0.01")
    payload = []
    for plan in plans:
        slot = groups[plan_charge_group_key(plan)]
        pix_plan = slot.get(PlanPaymentMethod.PIX)
        card_plan = slot.get(PlanPaymentMethod.CREDIT_CARD)
        charge_pix = str(pix_plan.price.quantize(cent)) if pix_plan else "0.00"
        charge_card = str(card_plan.price.quantize(cent)) if card_plan else "0.00"
        tier = resolve_commercial_tier(
            is_family_plan=plan.is_family_plan, is_loyalty_plan=plan.is_loyalty_plan
        )
        payload.append(
            {
                "id": (
                    build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, plan.pk)
                    if prefixed
                    else plan.pk
                ),
                "code": plan.code,
                "name": plan.display_name,
                "commercial_tier": tier,
                "commercial_tier_label": COMMERCIAL_TIER_LABELS.get(tier, tier),
                "price": str(plan.price),
                "charge_pix": charge_pix,
                "charge_card": charge_card,
                "monthly_reference_price": (
                    str(plan.monthly_reference_price)
                    if plan.monthly_reference_price is not None
                    else ""
                ),
                "cycle": plan.get_billing_cycle_display(),
                "billing_cycle": plan.billing_cycle,
                "payment_method": plan.payment_method,
                "payment_method_label": plan.get_payment_method_display(),
                "is_family_plan": plan.is_family_plan,
                "is_loyalty_plan": plan.is_loyalty_plan,
                "audience": plan.audience,
                "audience_label": plan.get_audience_display(),
                "weekly_frequency": plan.weekly_frequency,
                "weekly_frequency_label": plan.get_weekly_frequency_display(),
                "teacher_commission_percentage": str(plan.teacher_commission_percentage),
                "requires_special_authorization": plan.requires_special_authorization,
                "installment_label": build_installment_label(plan),
                "installment_count": (
                    CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
                    if plan.payment_method == "credit_card"
                    else 0
                ),
                "gateway_code": plan.gateway_code or "",
                "family_discount_percentage": "0",
            }
        )
    return payload


def _build_plan_price_catalog_payload():
    prices = list(
        PlanPrice.objects.filter(is_active=True, tier__is_active=True)
        .select_related("tier")
        .order_by("tier__display_order", "price")
    )
    cent = Decimal("0.01")
    payload = []
    for price in prices:
        own_price = str(price.price.quantize(cent))
        charge_pix = own_price if price.payment_method == PlanPaymentMethod.PIX else "0.00"
        charge_card = own_price if price.payment_method == PlanPaymentMethod.CREDIT_CARD else "0.00"
        payload.append(
            {
                "id": build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, price.pk),
                "code": f"{price.tier.code}-{price.gateway_code}-{price.billing_cycle}",
                "name": price.tier.display_name,
                "commercial_tier": "individual",
                "commercial_tier_label": COMMERCIAL_TIER_LABELS.get("individual", "Individual"),
                "price": str(price.price),
                "charge_pix": charge_pix,
                "charge_card": charge_card,
                "monthly_reference_price": (
                    str(price.monthly_reference_price)
                    if price.monthly_reference_price is not None
                    else ""
                ),
                "cycle": price.get_billing_cycle_display(),
                "billing_cycle": price.billing_cycle,
                "payment_method": price.payment_method,
                "payment_method_label": price.get_payment_method_display(),
                "is_family_plan": False,
                "is_loyalty_plan": False,
                "audience": price.tier.audience,
                "audience_label": price.tier.get_audience_display(),
                "weekly_frequency": price.tier.weekly_frequency,
                "weekly_frequency_label": price.tier.get_weekly_frequency_display(),
                "teacher_commission_percentage": str(price.teacher_commission_percentage),
                "requires_special_authorization": False,
                "installment_label": build_installment_label_for_price(price),
                "installment_count": (
                    CYCLE_INSTALLMENTS.get(price.billing_cycle, 1)
                    if price.payment_method == "credit_card"
                    else 0
                ),
                "gateway_code": price.gateway_code or "",
                "family_discount_percentage": str(price.tier.family_discount_percentage),
            }
        )
    return payload
