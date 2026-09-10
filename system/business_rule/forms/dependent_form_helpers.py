from system.business_rule.constants import DependentFinancialMode
from system.business_rule.models import ProductVariant
from system.business_rule.models.plan import PlanAudience
from system.business_rule.selectors.plan_eligibility import (
    PlanEligibilityContext,
    build_eligibility_context_for_person,
    classify_audience_from_age,
    classify_class_groups_audience,
)
from system.business_rule.services.membership import get_active_membership
from system.business_rule.services.membership_resolution import membership_is_family_plan


DEPENDENT_FLOW_KIND = "dependent_addition"


MATERIAL_FIELD_PREFIX = "material_variant_"


def owner_has_family_plan(owner):
    membership = get_active_membership(owner)
    return membership_is_family_plan(membership)


def resolve_financial_mode(cleaned_data):
    mode = cleaned_data.get("financial_mode") or ""
    allowed = {
        DependentFinancialMode.DEPENDENT_OWN,
        DependentFinancialMode.FAMILY_EXISTING,
        DependentFinancialMode.FAMILY_UPGRADE,
    }
    if mode in allowed:
        return mode
    if cleaned_data.get("use_family_plan"):
        return DependentFinancialMode.FAMILY_EXISTING
    return DependentFinancialMode.DEPENDENT_OWN


def build_family_upgrade_context(owner, cleaned_data):
    base = build_eligibility_context_for_person(owner)
    adult_active_count = base.resolved_adult_active_count
    kids_count = base.kids_juvenile_active_count
    dependent_audience = classify_dependent_audience(cleaned_data)
    if dependent_audience == PlanAudience.ADULT:
        adult_active_count += 1
    elif dependent_audience == PlanAudience.KIDS_JUVENILE:
        kids_count += 1
    return PlanEligibilityContext(
        adult_active=adult_active_count > 0,
        adult_active_count=adult_active_count,
        kids_juvenile_active_count=kids_count,
        allow_special_authorization=False,
        veteran_eligible=base.veteran_eligible,
    )


def classify_dependent_audience(cleaned_data):
    adult_active, kids_count = classify_class_groups_audience(
        cleaned_data.get("resolved_class_groups") or []
    )
    if adult_active:
        return PlanAudience.ADULT
    if kids_count:
        return PlanAudience.KIDS_JUVENILE
    return classify_audience_from_age(cleaned_data.get("dependent_birthdate"))


def build_material_variant_field_name(variant_id):
    return f"{MATERIAL_FIELD_PREFIX}{variant_id}"


def get_material_variants():
    return list(
        ProductVariant.objects.select_related("product", "product__category")
        .filter(
            is_active=True,
            stock_quantity__gt=0,
            product__is_active=True,
            product__category__is_active=True,
        )
        .order_by(
            "product__category__display_order",
            "product__category__display_name",
            "product__display_name",
            "color",
            "size",
            "pk",
        )
    )
