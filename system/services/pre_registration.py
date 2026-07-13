import json

from system.constants import CheckoutAction
from system.models.pre_registration import PreRegistration, PreRegistrationStatus

MULTI_VALUE_FORM_FIELDS = frozenset({
    "holder_class_groups",
    "dependent_class_groups",
    "student_class_groups",
})


def build_wizard_form_snapshot(post_data) -> dict:
    snapshot = {}
    for key, values in post_data.lists():
        if key == "csrfmiddlewaretoken":
            continue
        if key in MULTI_VALUE_FORM_FIELDS:
            snapshot[key] = values
        else:
            snapshot[key] = values if len(values) > 1 else values[0]
    return snapshot


def snapshot_scalar(snapshot, key, default=""):
    value = snapshot.get(key, default)
    if isinstance(value, list):
        value = value[0] if value else default
    return value or default


def resolve_primary_cpf(cleaned_data):
    return (
        cleaned_data.get("holder_cpf")
        or cleaned_data.get("guardian_cpf")
        or cleaned_data.get("other_cpf")
        or ""
    )


def resolve_primary_email(cleaned_data):
    return (
        cleaned_data.get("holder_email")
        or cleaned_data.get("guardian_email")
        or cleaned_data.get("other_email")
        or ""
    )


def _legacy_plan_pk_from_catalog_id(catalog_id):
    if not catalog_id:
        return None
    from system.services.registration_checkout import resolve_catalog_plan

    legacy_plan, _ = resolve_catalog_plan(catalog_id)
    return legacy_plan.pk if legacy_plan is not None else None


def save_pre_registration_from_form(session, post_data, cleaned_data):
    snapshot = build_wizard_form_snapshot(post_data)
    if not session.session_key:
        session.create()
    pre_registration_id = session.get("pending_pre_registration_id")
    defaults = {
        "session_key": session.session_key or "",
        "registration_profile": cleaned_data.get("registration_profile", ""),
        "holder_cpf": resolve_primary_cpf(cleaned_data),
        "holder_email": resolve_primary_email(cleaned_data),
        "form_snapshot": snapshot,
        "selected_plan_id": _legacy_plan_pk_from_catalog_id(cleaned_data.get("selected_plan")),
        "checkout_action": cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER,
        "status": PreRegistrationStatus.DRAFT,
    }
    if pre_registration_id:
        updated = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if updated is not None and updated.status != PreRegistrationStatus.FINALIZED:
            for key, value in defaults.items():
                setattr(updated, key, value)
            updated.save()
            return updated
    return PreRegistration.objects.create(**defaults)


def mark_pre_registration_trial_requested(pre_registration):
    snapshot = pre_registration.form_snapshot or {}
    snapshot["trial_requested"] = True
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])
    return pre_registration


def get_pending_person_summary(session):
    pre_registration_id = session.get("pending_pre_registration_id")
    if not pre_registration_id:
        return None
    pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
    if pre_registration is None:
        return None
    return build_pending_summary_from_pre_registration(pre_registration)


def build_pending_summary_from_pre_registration(pre_registration):
    data = pre_registration.form_snapshot or {}
    profile = data.get("registration_profile") or pre_registration.registration_profile
    is_guardian = profile == "guardian"
    base_prefix = "guardian" if is_guardian else "holder"
    base = {
        "id": None,
        "full_name": data.get(f"{base_prefix}_name", ""),
        "email": data.get(f"{base_prefix}_email", ""),
        "phone": data.get(f"{base_prefix}_phone", ""),
        **build_snapshot_class_group_summary(
            data.get(f"{base_prefix}_class_groups") or []
        ),
        "person_type_code": "guardian" if is_guardian else "student",
    }
    students = []
    if is_guardian and data.get("student_name"):
        students.append(build_snapshot_student_summary(data, "student"))
    if (not is_guardian) and data.get("dependent_name"):
        students.append(build_snapshot_student_summary(data, "dependent"))
    for dependent in get_extra_dependents_from_snapshot(data):
        if dependent.get("full_name"):
            students.append(build_extra_dependent_summary(dependent))
    if students:
        base["students"] = students
    return base


def build_snapshot_student_summary(snapshot, prefix):
    return {
        "full_name": snapshot_scalar(snapshot, f"{prefix}_name", ""),
        **build_snapshot_class_group_summary(
            snapshot.get(f"{prefix}_class_groups") or []
        ),
    }


def build_extra_dependent_summary(dependent):
    return {
        "full_name": dependent.get("full_name", ""),
        **build_snapshot_class_group_summary(
            dependent.get("class_groups") or []
        ),
    }


def get_extra_dependents_from_snapshot(snapshot):
    raw_payload = snapshot.get("extra_dependents_payload") or []
    if isinstance(raw_payload, list):
        return raw_payload
    try:
        parsed = json.loads(raw_payload)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def build_snapshot_class_group_summary(raw_values):
    from system.services.class_overview import resolve_class_group_selection

    if isinstance(raw_values, str):
        raw_values = [raw_values]
    return build_class_group_summary_from_groups(
        resolve_class_group_selection(raw_values, allow_inactive=True)
    )


def build_class_group_summary_from_groups(groups):
    from system.services.class_overview import build_class_group_filter_value

    class_group_ids = []
    class_group_names = []
    for class_group in groups:
        class_group_value = build_class_group_filter_value(
            class_group.class_category_id,
            class_group.display_name,
        )
        if class_group_value not in class_group_ids:
            class_group_ids.append(class_group_value)
        class_group_name = str(class_group)
        if class_group_name not in class_group_names:
            class_group_names.append(class_group_name)
    return {
        "class_group_name": ", ".join(class_group_names),
        "class_group_ids": class_group_ids,
    }


def get_order_summary(order_id):
    from system.models.registration_order import RegistrationOrder

    if not order_id:
        return None
    try:
        order = RegistrationOrder.objects.prefetch_related("items").select_related("plan").get(pk=order_id)
    except RegistrationOrder.DoesNotExist:
        return None
    items = [
        {
            "name": item.product_name,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "subtotal": str(item.subtotal),
        }
        for item in order.items.all()
    ]
    return {
        "id": order.pk,
        "plan_name": order.plan.display_name if order.plan else None,
        "plan_price": str(order.plan_price) if order.plan_price else None,
        "total": str(order.total),
        "items": items,
    }


def get_registration_order_or_pre_registration_summary(session, kind):
    order_key = "plan_order_id" if kind == "plan" else "materials_order_id"
    order_summary = get_order_summary(session.get(order_key))
    if order_summary:
        return order_summary
    pre_registration_id = session.get("pending_pre_registration_id")
    if not pre_registration_id:
        return None
    pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
    if pre_registration is None:
        return None
    snapshot = pre_registration.form_snapshot or {}
    if kind == "plan":
        plan_payment = snapshot.get("plan_payment") or {}
        items = plan_payment.get("items") or []
        return {
            "id": None,
            "plan_name": " + ".join(item.get("plan_name", "") for item in items if item.get("plan_name")),
            "plan_price": plan_payment.get("total"),
            "total": plan_payment.get("total"),
            "items": items,
        }
    materials_payment = snapshot.get("materials_payment") or {}
    return {
        "id": None,
        "plan_name": None,
        "plan_price": None,
        "total": materials_payment.get("total"),
        "items": materials_payment.get("items") or [],
    }


def normalize_snapshot_for_form(snapshot):
    result = {}
    for key, value in snapshot.items():
        if isinstance(value, dict):
            continue
        if key in MULTI_VALUE_FORM_FIELDS:
            if isinstance(value, list):
                result[key] = value
            elif value:
                result[key] = [value]
            else:
                result[key] = []
        elif isinstance(value, list):
            result[key] = value[0] if value else ""
        else:
            result[key] = value
    return result


def grant_trial_for_pre_registration(pre_registration, primary_person):
    from decimal import Decimal
    from system.models.registration_order import (
        OrderKind, PaymentProvider, PaymentStatus, RegistrationOrder,
    )
    from system.models.plan import SubscriptionPlan
    from system.services.trial_access import grant_trial_for_order

    plan = None
    if pre_registration.selected_plan_id:
        plan = SubscriptionPlan.objects.filter(pk=pre_registration.selected_plan_id).first()

    trial_order = RegistrationOrder.objects.create(
        person=primary_person,
        plan=plan,
        kind=OrderKind.SUBSCRIPTION,
        payment_status=PaymentStatus.PENDING,
        payment_provider=PaymentProvider.NONE,
        total=plan.price if plan else Decimal("0"),
        plan_price=plan.price if plan else Decimal("0"),
        notes="Aula experimental via pré-cadastro.",
    )
    grant_trial_for_order(trial_order, notes="Aula experimental concedida no pré-cadastro.")
    return trial_order


def finalize_pre_registration(pre_registration):
    from system.services.registration_finalize import RegistrationFinalizeService

    return RegistrationFinalizeService.create_from_pre_registration(pre_registration)
