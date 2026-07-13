from django.db import transaction
from django.utils import timezone

from system.constants import (
    CheckoutAction,
    DependentCardStrategy,
    DependentFinancialMode,
    PersonTypeCode,
)
from system.models import (
    Membership,
    MembershipStatus,
    PaymentProvider,
    PaymentStatus,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PreRegistration,
    PreRegistrationStatus,
    RegistrationOrder,
)
from system.services.financial_transactions import (
    apply_order_financials,
    resolve_checkout_action_for_plan,
)
from system.services.membership import activate_membership_from_paid_order
from system.services.registration import (
    _create_person_with_account,
    _create_relationship,
    ensure_default_person_types,
)
from system.services.registration_checkout import (
    apply_order_variant_stock,
    create_pre_registration_materials_payment,
    create_pre_registration_plan_payment,
    create_product_only_order,
    resolve_selected_product_items,
)


DEPENDENT_FLOW_KIND = "dependent_addition"
MATERIALS_ORDER_MARKER_PREFIX = "[dependent_materials_pre_registration:"


def _legacy_selected_plan(cleaned_data):
    from system.models.plan import PlanPrice

    plan = cleaned_data.get("selected_plan_obj")
    if plan is None or isinstance(plan, PlanPrice):
        return None
    return plan


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
        selected_plan=_legacy_selected_plan(cleaned_data),
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
    pre_registration.selected_plan = _legacy_selected_plan(cleaned_data)
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
    dependent = _create_person_with_account(
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
    _create_relationship(
        source_person=owner,
        target_person=dependent,
        kinship_type=cleaned_data.get("dependent_kinship_type", ""),
        kinship_other_label=cleaned_data.get("dependent_kinship_other_label", ""),
    )
    from system.services.membership_timeline import record_membership_event
    from system.models.membership_timeline import MembershipTimelineEventType

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
        order = _create_paid_plan_order(
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
        order = _create_paid_family_upgrade_order(
            owner,
            dependent,
            cleaned_data["selected_plan_obj"],
            checkout_action=cleaned_data.get("checkout_action") or "",
        )

    if pre_registration is not None:
        _create_paid_materials_order_if_needed(dependent, pre_registration)
        pre_registration.mark_finalized(dependent)
    return {
        "dependent": dependent,
        "order": order,
        "already_finalized": False,
    }


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
        from system.services.registration_checkout import (
            CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
            build_catalog_plan_id,
        )

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
        from system.services.registration_checkout import resolve_catalog_plan

        legacy_plan, plan_price = resolve_catalog_plan(snapshot_plan_id)
        cleaned_data["selected_plan"] = str(snapshot_plan_id)
        cleaned_data["selected_plan_obj"] = legacy_plan or plan_price
    elif pre_registration and pre_registration.selected_plan_id:
        cleaned_data["selected_plan"] = str(pre_registration.selected_plan_id)
        cleaned_data["selected_plan_obj"] = pre_registration.selected_plan

    if pre_registration and pre_registration.checkout_action:
        cleaned_data["checkout_action"] = pre_registration.checkout_action


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
    for item in _material_payload_from_snapshot(snapshot):
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


def _create_paid_plan_order(
    dependent, plan, *, checkout_action="",
    stripe_subscription_id="", stripe_subscription_item_id="", stripe_customer_id="",
):
    from system.models.plan import PlanPrice
    from system.services.family_pricing import recompute_family_discounts_for_person

    is_plan_price = isinstance(plan, PlanPrice)
    order = RegistrationOrder.objects.create(
        person=dependent,
        plan=None if is_plan_price else plan,
        plan_price_ref=plan if is_plan_price else None,
        plan_price=plan.price,
        total=plan.price,
        payment_status=PaymentStatus.PAID,
        paid_at=timezone.now(),
        payment_provider=(
            PaymentProvider.STRIPE
            if checkout_action == CheckoutAction.STRIPE_CARD
            else PaymentProvider.ASAAS
        ),
        notes="Pagamento confirmado no pré-cadastro de dependente.",
    )
    apply_order_financials(
        order,
        payment_provider=order.payment_provider,
        mark_available=True,
    )
    activate_membership_from_paid_order(
        order,
        notes="Dependente ativado após pagamento do pré-cadastro.",
        stripe_subscription_id=stripe_subscription_id,
        stripe_subscription_item_id=stripe_subscription_item_id,
        stripe_customer_id=stripe_customer_id,
    )
    recompute_family_discounts_for_person(dependent)
    return order


def _create_paid_family_upgrade_order(owner, dependent, plan, *, checkout_action=""):
    order = RegistrationOrder.objects.create(
        person=owner,
        plan=plan,
        plan_price=plan.price,
        total=plan.price,
        payment_status=PaymentStatus.PAID,
        paid_at=timezone.now(),
        payment_provider=(
            PaymentProvider.STRIPE
            if checkout_action == CheckoutAction.STRIPE_CARD
            else PaymentProvider.ASAAS
        ),
        notes=(
            "Upgrade familiar confirmado no pré-cadastro de dependente: "
            f"{dependent.full_name}."
        ),
    )
    apply_order_financials(
        order,
        payment_provider=order.payment_provider,
        mark_available=True,
    )
    membership = activate_membership_from_paid_order(
        order,
        notes="Titular migrado para plano familiar após pagamento do dependente.",
    )
    _retire_previous_owner_memberships(owner, keep_membership=membership)
    return order


def _retire_previous_owner_memberships(owner, *, keep_membership):
    if keep_membership is None:
        return
    now = timezone.now()
    memberships = (
        Membership.objects.filter(
            person=owner,
            status__in=(
                MembershipStatus.PENDING,
                MembershipStatus.ACTIVE,
                MembershipStatus.PAST_DUE,
                MembershipStatus.EXEMPTED,
            ),
        )
        .exclude(pk=keep_membership.pk)
        .order_by("pk")
    )
    for membership in memberships:
        membership.status = MembershipStatus.CANCELED
        membership.canceled_at = membership.canceled_at or now
        membership.notes = (
            (membership.notes or "")
            + f"\nSubstituída pelo plano familiar #{keep_membership.pk}."
        ).strip()
        membership.save(
            update_fields=("status", "canceled_at", "notes", "updated_at")
        )


def _create_paid_materials_order_if_needed(dependent, pre_registration):
    snapshot = pre_registration.form_snapshot or {}
    if not snapshot.get("materials_paid"):
        return None
    marker = _materials_order_marker(pre_registration.pk)
    existing = RegistrationOrder.objects.filter(
        person=dependent,
        notes__contains=marker,
    ).first()
    if existing is not None:
        return existing

    payload = _material_payload_from_snapshot(snapshot)
    if not payload:
        return None
    selections = resolve_selected_product_items(payload)
    order = create_product_only_order(dependent, selections)
    if order is None:
        return None
    order.payment_status = PaymentStatus.PAID
    order.payment_provider = PaymentProvider.ASAAS
    order.paid_at = timezone.now()
    order.notes = "\n".join(
        line for line in (order.notes, marker) if line
    )
    order.save(
        update_fields=(
            "payment_status",
            "payment_provider",
            "paid_at",
            "notes",
            "updated_at",
        )
    )
    apply_order_financials(
        order,
        payment_provider=PaymentProvider.ASAAS,
        mark_available=True,
    )
    apply_order_variant_stock(order)
    return order


def _materials_order_marker(pre_registration_id):
    return f"{MATERIALS_ORDER_MARKER_PREFIX}{pre_registration_id}]"


def _material_payload_from_snapshot(snapshot):
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
    from system.models.plan import PlanPrice
    from system.services.registration_checkout import (
        CATALOG_ID_PREFIX_PLAN_PRICE,
        CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
        build_catalog_plan_id,
    )

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
