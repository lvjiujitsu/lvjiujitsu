from system.business_rule.constants import DependentFinancialMode
from system.business_rule.services.registration_checkout import resolve_catalog_plan
from system.business_rule.services.registration_checkout import CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, build_catalog_plan_id
from system.business_rule.services.registration_checkout import (
    CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
    build_catalog_plan_id,
)


def is_dependent_payment_confirmed(pre_registration):
    if pre_registration is None:
        return False
    snapshot = pre_registration.form_snapshot or {}
    return pre_registration.payment_confirmed or bool(snapshot.get("plan_paid"))


def is_dependent_materials_confirmed(pre_registration):
    if pre_registration is None:
        return False
    snapshot = pre_registration.form_snapshot or {}
    return bool(snapshot.get("materials_paid"))


def restore_confirmed_payment_post_data(post_data, pre_registration):
    snapshot = (pre_registration.form_snapshot or {}) if pre_registration else {}
    financial_mode = (
        snapshot.get("financial_mode") or DependentFinancialMode.DEPENDENT_OWN
    )
    post_data["financial_mode"] = financial_mode
    if financial_mode == DependentFinancialMode.FAMILY_EXISTING:
        post_data["use_family_plan"] = "on"
    elif "use_family_plan" in post_data:
        del post_data["use_family_plan"]

    selected_plan_id = ""
    if snapshot.get("selected_plan"):
        selected_plan_id = str(snapshot.get("selected_plan"))
    elif pre_registration and pre_registration.selected_plan_id:

        selected_plan_id = build_catalog_plan_id(
            CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, pre_registration.selected_plan_id
        )
    if selected_plan_id:
        post_data["selected_plan"] = selected_plan_id

    checkout_action = ""
    if pre_registration and pre_registration.checkout_action:
        checkout_action = pre_registration.checkout_action
    elif snapshot.get("checkout_action"):
        checkout_action = snapshot.get("checkout_action")
    if checkout_action:
        post_data["checkout_action"] = checkout_action


def apply_confirmed_payment_to_cleaned_data(cleaned_data, pre_registration):
    snapshot = (pre_registration.form_snapshot or {}) if pre_registration else {}
    financial_mode = snapshot.get("financial_mode") or DependentFinancialMode.DEPENDENT_OWN
    cleaned_data["financial_mode"] = financial_mode
    cleaned_data["use_family_plan"] = financial_mode == DependentFinancialMode.FAMILY_EXISTING

    snapshot_plan_id = snapshot.get("selected_plan") or ""
    if snapshot_plan_id:

        legacy_plan, plan_price = resolve_catalog_plan(snapshot_plan_id)
        cleaned_data["selected_plan"] = str(snapshot_plan_id)
        cleaned_data["selected_plan_obj"] = legacy_plan or plan_price
    elif pre_registration and pre_registration.selected_plan_id:
        cleaned_data["selected_plan"] = str(pre_registration.selected_plan_id)
        cleaned_data["selected_plan_obj"] = pre_registration.selected_plan

    if pre_registration and pre_registration.checkout_action:
        cleaned_data["checkout_action"] = pre_registration.checkout_action
