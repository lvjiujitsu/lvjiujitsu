from system.business_rule.constants import (
    CheckoutAction,
    DependentCardStrategy,
    DependentFinancialMode,
)
from system.business_rule.services.registration_checkout import CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, build_catalog_plan_id
from system.business_rule.services.registration_checkout import CATALOG_ID_PREFIX_PLAN_PRICE, CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, build_catalog_plan_id
from system.business_rule.models.plan import PlanPrice


DEPENDENT_FLOW_KIND = "dependent_addition"


MATERIALS_ORDER_MARKER_PREFIX = "[dependent_materials_pre_registration:"


def legacy_selected_plan(cleaned_data):

    plan = cleaned_data.get("selected_plan_obj")
    if plan is None or isinstance(plan, PlanPrice):
        return None
    return plan


def build_dependent_snapshot(owner, cleaned_data):
    snapshot = {
        "flow_kind": DEPENDENT_FLOW_KIND,
        "owner_person_id": owner.pk,
        "registration_profile": "dependent",
        "holder_name": owner.full_name,
        "holder_cpf": owner.cpf,
        "holder_email": owner.email or "",
        "holder_phone": owner.phone or "",
        "dependent_name": cleaned_data.get("dependent_name") or "",
        "dependent_cpf": cleaned_data.get("dependent_cpf") or "",
        "dependent_birthdate": _date_to_string(cleaned_data.get("dependent_birthdate")),
        "dependent_biological_sex": cleaned_data.get("dependent_biological_sex") or "",
        "dependent_email": cleaned_data.get("dependent_email") or "",
        "dependent_phone": cleaned_data.get("dependent_phone") or "",
        "dependent_kinship_type": cleaned_data.get("dependent_kinship_type") or "",
        "dependent_kinship_other_label": cleaned_data.get(
            "dependent_kinship_other_label"
        )
        or "",
        "dependent_class_groups": list(cleaned_data.get("dependent_class_groups") or []),
        "dependent_blood_type": cleaned_data.get("dependent_blood_type") or "",
        "dependent_allergies": cleaned_data.get("dependent_allergies") or "",
        "dependent_injuries": cleaned_data.get("dependent_injuries") or "",
        "dependent_emergency_contact": cleaned_data.get("dependent_emergency_contact") or "",
        "dependent_has_martial_art": cleaned_data.get("dependent_has_martial_art") or "",
        "dependent_martial_art": cleaned_data.get("dependent_martial_art") or "",
        "dependent_martial_art_graduation": cleaned_data.get(
            "dependent_martial_art_graduation"
        )
        or "",
        "dependent_jiu_jitsu_belt": cleaned_data.get("dependent_jiu_jitsu_belt") or "",
        "dependent_jiu_jitsu_stripes": cleaned_data.get("dependent_jiu_jitsu_stripes"),
        "dependent_martial_art_started_at": _date_to_string(
            cleaned_data.get("dependent_martial_art_started_at")
        ),
        "dependent_martial_art_last_graduation_at": _date_to_string(
            cleaned_data.get("dependent_martial_art_last_graduation_at")
        ),
        "dependent_previous_academy": cleaned_data.get("dependent_previous_academy") or "",
        "financial_mode": cleaned_data.get("financial_mode")
        or DependentFinancialMode.DEPENDENT_OWN,
        "card_strategy": cleaned_data.get("card_strategy")
        or DependentCardStrategy.NEW_CARD,
        "selected_plan": cleaned_data.get("selected_plan") or "",
        "selected_plans_payload": _selected_plans_payload(owner, cleaned_data),
        "checkout_action": cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER,
        "selected_products_payload": list(
            cleaned_data.get("selected_products_payload") or []
        ),
        "materials_checkout_action": (
            cleaned_data.get("materials_checkout_action") or CheckoutAction.PAY_LATER
        ),
    }
    return snapshot


def materials_order_marker(pre_registration_id):
    return f"{MATERIALS_ORDER_MARKER_PREFIX}{pre_registration_id}]"


def material_payload_from_snapshot(snapshot):
    payload = snapshot.get("selected_products_payload") or []
    if not isinstance(payload, list):
        return []
    items = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            variant_id = int(item.get("variant_id") or 0)
            quantity = int(item.get("quantity") or item.get("qty") or 0)
        except (TypeError, ValueError):
            continue
        if variant_id > 0 and quantity > 0:
            items.append({"variant_id": variant_id, "quantity": quantity})
    return items


def _date_to_string(value):
    if not value:
        return ""
    return value.isoformat()


def _selected_plans_payload(owner, cleaned_data):

    plan = cleaned_data.get("selected_plan_obj")
    if plan is None:
        return []
    prefix = (
        CATALOG_ID_PREFIX_PLAN_PRICE
        if isinstance(plan, PlanPrice)
        else CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN
    )
    plan_id = build_catalog_plan_id(prefix, plan.pk)
    financial_mode = (
        cleaned_data.get("financial_mode") or DependentFinancialMode.DEPENDENT_OWN
    )
    if financial_mode == DependentFinancialMode.FAMILY_UPGRADE:
        return [
            {
                "person": "owner",
                "label": (
                    f"{owner.full_name} + "
                    f"{cleaned_data.get('dependent_name') or 'Dependente'}"
                ),
                "plan_id": plan_id,
            }
        ]
    return [
        {
            "person": "dependent",
            "label": cleaned_data.get("dependent_name") or "Dependente",
            "plan_id": plan_id,
        }
    ]
