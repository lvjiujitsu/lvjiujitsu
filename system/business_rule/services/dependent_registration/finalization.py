from django.db import transaction
from system.business_rule.constants import DependentFinancialMode, PersonTypeCode
from system.business_rule.models import PreRegistration, PreRegistrationStatus
from system.business_rule.services.financial_transactions import resolve_checkout_action_for_plan
from system.business_rule.services.registration import (
    create_person_with_account,
    create_relationship,
    ensure_default_person_types,
)
from system.business_rule.services.registration_checkout import (
    create_pre_registration_materials_payment,
    create_pre_registration_plan_payment,
)
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.models.membership_timeline import MembershipTimelineEventType
from system.business_rule.services.dependent_registration.orders import create_paid_family_upgrade_order, create_paid_materials_order_if_needed, create_paid_plan_order
from system.business_rule.services.dependent_registration.payment_state import apply_confirmed_payment_to_cleaned_data, is_dependent_materials_confirmed, is_dependent_payment_confirmed
from system.business_rule.services.dependent_registration.pre_registration import create_dependent_pre_registration, get_owned_dependent_by_cpf, save_checkout_url, update_dependent_pre_registration


@transaction.atomic
def finalize_dependent_registration(owner, cleaned_data, *, pre_registration=None):
    if pre_registration is not None:
        pre_registration = (
            PreRegistration.objects.select_for_update()
            .select_related("finalized_person")
            .get(pk=pre_registration.pk)
        )
        if pre_registration.status == PreRegistrationStatus.FINALIZED:
            return {
                "dependent": pre_registration.finalized_person,
                "order": None,
                "already_finalized": True,
            }

    existing = get_owned_dependent_by_cpf(
        owner,
        cleaned_data.get("dependent_cpf") or "",
    )
    if existing is not None:
        if pre_registration is not None:
            pre_registration.mark_finalized(existing)
        return {
            "dependent": existing,
            "order": None,
            "already_finalized": True,
        }

    person_types = ensure_default_person_types()
    dependent = create_person_with_account(
        full_name=cleaned_data["dependent_name"],
        cpf=cleaned_data["dependent_cpf"],
        email=cleaned_data.get("dependent_email", ""),
        phone=cleaned_data.get("dependent_phone", ""),
        birth_date=cleaned_data.get("dependent_birthdate"),
        biological_sex=cleaned_data.get("dependent_biological_sex", ""),
        password=cleaned_data["dependent_password"],
        person_type=person_types[PersonTypeCode.DEPENDENT],
        blood_type=cleaned_data.get("dependent_blood_type", ""),
        allergies=cleaned_data.get("dependent_allergies", ""),
        previous_injuries=cleaned_data.get("dependent_injuries", ""),
        emergency_contact=cleaned_data.get("dependent_emergency_contact", ""),
        martial_art=cleaned_data.get("dependent_martial_art", ""),
        martial_art_graduation=cleaned_data.get("dependent_martial_art_graduation", ""),
        jiu_jitsu_belt=cleaned_data.get("dependent_jiu_jitsu_belt", ""),
        jiu_jitsu_stripes=cleaned_data.get("dependent_jiu_jitsu_stripes"),
        martial_art_started_at=cleaned_data.get("dependent_martial_art_started_at"),
        martial_art_last_graduation_at=cleaned_data.get(
            "dependent_martial_art_last_graduation_at"
        ),
        previous_academy=cleaned_data.get("dependent_previous_academy", ""),
        class_groups=cleaned_data.get("resolved_class_groups", []),
    )
    create_relationship(
        source_person=owner,
        target_person=dependent,
        kinship_type=cleaned_data.get("dependent_kinship_type", ""),
        kinship_other_label=cleaned_data.get("dependent_kinship_other_label", ""),
    )

    record_membership_event(
        owner,
        MembershipTimelineEventType.DEPENDENT_ADDED,
        actor=owner,
        context={"dependent_name": dependent.full_name},
    )
    record_membership_event(
        dependent,
        MembershipTimelineEventType.DEPENDENT_ADDED,
        actor=owner,
        context={"dependent_name": dependent.full_name},
    )
    dependent.is_active = True
    dependent.save(update_fields=["is_active", "updated_at"])
    account = dependent.access_account
    account.is_active = True
    account.save(update_fields=["is_active", "updated_at"])

    order = None
    financial_mode = cleaned_data.get("financial_mode") or (
        DependentFinancialMode.FAMILY_EXISTING
        if cleaned_data.get("use_family_plan")
        else DependentFinancialMode.DEPENDENT_OWN
    )
    if (
        financial_mode == DependentFinancialMode.DEPENDENT_OWN
        and cleaned_data.get("selected_plan_obj")
    ):
        plan_payment = (
            (pre_registration.form_snapshot or {}).get("plan_payment") or {}
            if pre_registration is not None
            else {}
        )
        order = create_paid_plan_order(
            dependent,
            cleaned_data["selected_plan_obj"],
            checkout_action=cleaned_data.get("checkout_action") or "",
            stripe_subscription_id=plan_payment.get("stripe_subscription_id", ""),
            stripe_subscription_item_id=plan_payment.get("stripe_subscription_item_id", ""),
            stripe_customer_id=plan_payment.get("stripe_customer_id", ""),
        )
    elif (
        financial_mode == DependentFinancialMode.FAMILY_UPGRADE
        and cleaned_data.get("selected_plan_obj")
    ):
        order = create_paid_family_upgrade_order(
            owner,
            dependent,
            cleaned_data["selected_plan_obj"],
            checkout_action=cleaned_data.get("checkout_action") or "",
        )

    if pre_registration is not None:
        create_paid_materials_order_if_needed(dependent, pre_registration)
        pre_registration.mark_finalized(dependent)
    return {
        "dependent": dependent,
        "order": order,
        "already_finalized": False,
    }


def process_dependent_registration_submission(*, owner, form, pending, session):
    if form.existing_owned_dependent is not None:
        session.pop("pending_dependent_pre_registration_id", None)
        return {"kind": "existing_owned"}

    cleaned_data = form.cleaned_data
    payment_confirmed = is_dependent_payment_confirmed(pending)
    materials_confirmed = is_dependent_materials_confirmed(pending)
    if payment_confirmed:
        apply_confirmed_payment_to_cleaned_data(cleaned_data, pending)

    selected_materials = cleaned_data.get("selected_product_items") or []
    if (
        (cleaned_data.get("use_family_plan") or payment_confirmed)
        and selected_materials
        and not materials_confirmed
    ):
        if session.session_key is None:
            session.save()
        if pending is None:
            pending = create_dependent_pre_registration(
                owner, cleaned_data, session_key=session.session_key or ""
            )
        else:
            pending = update_dependent_pre_registration(pending, owner, cleaned_data)
        session["pending_dependent_pre_registration_id"] = pending.pk
        checkout_url = create_pre_registration_materials_payment(
            pending,
            selected_materials,
            cleaned_data["materials_checkout_action"],
        )
        save_checkout_url(pending, "materials", checkout_url)
        return {"kind": "materials_checkout", "checkout_url": checkout_url}

    if cleaned_data.get("use_family_plan") or payment_confirmed:
        finalize_dependent_registration(owner, cleaned_data, pre_registration=pending)
        session.pop("pending_dependent_pre_registration_id", None)
        return {"kind": "finalized"}

    checkout_action = cleaned_data.get("checkout_action")
    if not checkout_action or checkout_action == "pay_later":
        checkout_action = resolve_checkout_action_for_plan(
            cleaned_data.get("selected_plan_obj")
        )
    if checkout_action == "pay_later":
        return {"kind": "checkout_action_missing"}

    if session.session_key is None:
        session.save()
    pre_registration = create_dependent_pre_registration(
        owner, cleaned_data, session_key=session.session_key or ""
    )
    session["pending_dependent_pre_registration_id"] = pre_registration.pk
    existing_checkout_url = (pre_registration.form_snapshot or {}).get(
        "plan_checkout_url"
    )
    if pre_registration.is_awaiting_payment and existing_checkout_url:
        return {"kind": "plan_checkout", "checkout_url": existing_checkout_url}
    checkout_url = create_pre_registration_plan_payment(
        pre_registration,
        checkout_action,
        card_strategy=cleaned_data.get("card_strategy"),
        owner=owner,
    )
    save_checkout_url(pre_registration, "plan", checkout_url)
    pre_registration.mark_awaiting_payment()
    return {"kind": "plan_checkout", "checkout_url": checkout_url}
