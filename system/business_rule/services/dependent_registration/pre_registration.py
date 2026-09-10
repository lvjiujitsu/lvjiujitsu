from system.business_rule.constants import CheckoutAction
from system.business_rule.models import (
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PreRegistration,
    PreRegistrationStatus,
)
from system.business_rule.services.dependent_registration.snapshot import DEPENDENT_FLOW_KIND, legacy_selected_plan, material_payload_from_snapshot, build_dependent_snapshot


def create_dependent_pre_registration(owner, cleaned_data, *, session_key=""):
    existing = find_dependent_pre_registration(
        owner,
        cleaned_data.get("dependent_cpf") or "",
    )
    if existing is not None:
        return update_dependent_pre_registration(existing, owner, cleaned_data)
    snapshot = build_dependent_snapshot(owner, cleaned_data)
    return PreRegistration.objects.create(
        session_key=session_key or "",
        registration_profile="dependent",
        holder_cpf=owner.cpf,
        holder_email=owner.email,
        form_snapshot=snapshot,
        selected_plan=legacy_selected_plan(cleaned_data),
        checkout_action=cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER,
        status=PreRegistrationStatus.DRAFT,
    )


def update_dependent_pre_registration(pre_registration, owner, cleaned_data):
    snapshot = build_dependent_snapshot(owner, cleaned_data)
    current_snapshot = pre_registration.form_snapshot or {}
    for key in (
        "plan_payment",
        "plan_checkout_url",
        "plan_paid",
        "materials_payment",
        "materials_checkout_url",
        "materials_paid",
    ):
        if key in current_snapshot and key not in snapshot:
            snapshot[key] = current_snapshot[key]
    pre_registration.form_snapshot = snapshot
    pre_registration.selected_plan = legacy_selected_plan(cleaned_data)
    pre_registration.checkout_action = (
        cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
    )
    pre_registration.save(
        update_fields=(
            "form_snapshot",
            "selected_plan",
            "checkout_action",
            "updated_at",
        )
    )
    return pre_registration


def find_dependent_pre_registration(owner, dependent_cpf):
    if owner is None or not dependent_cpf:
        return None
    queryset = PreRegistration.objects.filter(
        registration_profile="dependent",
        holder_cpf=owner.cpf,
        status__in=(
            PreRegistrationStatus.DRAFT,
            PreRegistrationStatus.AWAITING_PAYMENT,
            PreRegistrationStatus.PAYMENT_CONFIRMED,
        ),
    ).order_by("-created_at")
    for pre_registration in queryset:
        snapshot = pre_registration.form_snapshot or {}
        if snapshot.get("flow_kind") != DEPENDENT_FLOW_KIND:
            continue
        if snapshot.get("owner_person_id") != owner.pk:
            continue
        if snapshot.get("dependent_cpf") == dependent_cpf:
            return pre_registration
    return None


def get_owned_dependent_by_cpf(owner, cpf):
    if owner is None or not cpf:
        return None
    dependent = Person.objects.filter(cpf=cpf, is_active=True).first()
    if dependent is None:
        return None
    if PersonRelationship.objects.filter(
        source_person=owner,
        target_person=dependent,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    ).exists():
        return dependent
    return None


def get_pending_dependent_pre_registration(session, owner):
    pre_registration_id = session.get("pending_dependent_pre_registration_id")
    if not pre_registration_id or owner is None:
        return None
    pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
    if pre_registration is None:
        return None
    snapshot = pre_registration.form_snapshot or {}
    if snapshot.get("flow_kind") != DEPENDENT_FLOW_KIND:
        return None
    if snapshot.get("owner_person_id") != owner.pk:
        return None
    return pre_registration


def initial_from_pre_registration(pre_registration):
    if pre_registration is None:
        return {}
    snapshot = dict(pre_registration.form_snapshot or {})
    initial = {
        key: value
        for key, value in snapshot.items()
        if key.startswith("dependent_")
        or key in {
            "financial_mode",
            "card_strategy",
            "selected_plan",
            "checkout_action",
            "materials_checkout_action",
        }
    }
    for item in material_payload_from_snapshot(snapshot):
        variant_id = item.get("variant_id")
        quantity = item.get("quantity")
        if variant_id and quantity:
            initial[f"material_variant_{variant_id}"] = quantity
    return initial


def save_checkout_url(pre_registration, stage, checkout_url):
    snapshot = pre_registration.form_snapshot or {}
    snapshot[f"{stage}_checkout_url"] = checkout_url
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])
    return pre_registration
