"""
Serviço de pré-cadastro.

Responsável por:
- Criar/atualizar PreRegistration a partir dos dados do wizard
- Restaurar o snapshot para re-popular o formulário
- Montar o resumo de pessoa pendente (pré-cadastro ou Person já criada)
- Finalizar: migrar os dados para a tabela Person
"""

import json

from django.utils import timezone

from system.constants import CheckoutAction
from system.models.pre_registration import PreRegistration, PreRegistrationStatus

# Campos sensíveis que não devem ser armazenados no snapshot
_EXCLUDED_SNAPSHOT_FIELDS = frozenset({
    "holder_password",
    "holder_password_confirm",
    "dependent_password",
    "dependent_password_confirm",
    "guardian_password",
    "guardian_password_confirm",
    "student_password",
    "student_password_confirm",
    "csrfmiddlewaretoken",
})

# Campos que o Django processa como lista (MultipleChoiceField) — sempre salvar como list no snapshot
MULTI_VALUE_FORM_FIELDS = frozenset({
    "holder_class_groups",
    "dependent_class_groups",
    "student_class_groups",
})


def build_form_snapshot(post_data: dict) -> dict:
    """
    Extrai do POST data apenas os campos relevantes do wizard,
    excluindo senhas e tokens CSRF.

    Args:
        post_data: QueryDict ou dict com os dados submetidos.

    Returns:
        dict seguro para armazenar no form_snapshot.
    """
    snapshot = {}
    for key, value in post_data.items():
        if key in _EXCLUDED_SNAPSHOT_FIELDS:
            continue
        # QueryDict pode ter listas (ex: class_groups MultipleChoiceField)
        if hasattr(post_data, "getlist"):
            values = post_data.getlist(key)
            snapshot[key] = values if len(values) > 1 else value
        else:
            snapshot[key] = value
    return snapshot


def build_wizard_form_snapshot(post_data) -> dict:
    """
    Constrói o snapshot do wizard a partir do POST bruto, preservando
    MultipleChoiceFields sempre como lista (mesmo com 1 valor).
    """
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
    """Lê um campo scalar do snapshot, normalizando caso tenha sido salvo como lista."""
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


def save_pre_registration_from_form(session, post_data, cleaned_data):
    """
    Cria ou atualiza o PreRegistration ativo da sessão a partir do form do wizard.

    Args:
        session: sessão Django (precisa de session_key, cria se ausente).
        post_data: QueryDict bruto do POST (para montar o snapshot completo).
        cleaned_data: form.cleaned_data já validado.

    Returns:
        A instância de PreRegistration criada ou atualizada.
    """
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
        "selected_plan_id": cleaned_data.get("selected_plan"),
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
    """Marca aula experimental no snapshot do pré-cadastro (fluxo 'pagar depois')."""
    snapshot = pre_registration.form_snapshot or {}
    snapshot["trial_requested"] = True
    pre_registration.form_snapshot = snapshot
    pre_registration.save(update_fields=["form_snapshot", "updated_at"])
    return pre_registration


def get_pre_registration_for_session(session_key: str) -> "PreRegistration | None":
    """
    Retorna o PreRegistration ativo (não finalizado, não abandonado)
    para a sessão dada, ou None se não existir.
    """
    return (
        PreRegistration.objects.filter(
            session_key=session_key,
            status__in=(
                PreRegistrationStatus.DRAFT,
                PreRegistrationStatus.AWAITING_PAYMENT,
                PreRegistrationStatus.PAYMENT_CONFIRMED,
            ),
        )
        .select_related("selected_plan", "plan_order", "finalized_person")
        .order_by("-created_at")
        .first()
    )


def create_or_update_pre_registration(
    session_key: str,
    post_data: dict,
    selected_plan=None,
    checkout_action: str = "",
) -> "PreRegistration":
    """
    Cria ou atualiza o PreRegistration para a sessão dada com os dados do wizard.

    Sempre sobrescreve o snapshot com os dados mais recentes.
    Não inclui senhas no snapshot.

    Args:
        session_key: chave da sessão Django.
        post_data: dados brutos do POST (QueryDict ou dict).
        selected_plan: instância de SubscriptionPlan, ou None.
        checkout_action: 'asaas_card' | 'pix' | 'pay_later' | ''.

    Returns:
        A instância de PreRegistration criada ou atualizada.
    """
    snapshot = build_form_snapshot(post_data)

    registration_profile = snapshot.get("registration_profile", "")
    holder_cpf = snapshot.get("holder_cpf", "")
    holder_email = snapshot.get("holder_email", "")

    pre_reg = get_pre_registration_for_session(session_key)

    if pre_reg is None:
        pre_reg = PreRegistration(session_key=session_key)

    pre_reg.registration_profile = registration_profile
    pre_reg.holder_cpf = holder_cpf
    pre_reg.holder_email = holder_email
    pre_reg.form_snapshot = snapshot
    if selected_plan is not None:
        pre_reg.selected_plan = selected_plan
    if checkout_action:
        pre_reg.checkout_action = checkout_action

    pre_reg.save()
    return pre_reg


def restore_form_initial(pre_reg: "PreRegistration") -> dict:
    """
    Converte o form_snapshot de um PreRegistration de volta para um dict
    de initial values adequado para o PortalRegistrationForm.

    Senhas são excluídas — o usuário precisará digitá-las novamente.

    Returns:
        dict com os valores iniciais para passar ao Form como `initial=`.
    """
    if not pre_reg or not pre_reg.form_snapshot:
        return {}
    return {k: v for k, v in pre_reg.form_snapshot.items()}


def get_pending_person_summary(session):
    """
    Resolve o resumo de pessoa pendente para exibir no wizard:
    a partir do PreRegistration ativo, ou — se já finalizado em fluxo legado —
    a partir da Person criada em sessão.
    """
    from system.models import Person, PersonRelationship, PersonRelationshipKind

    pre_registration_id = session.get("pending_pre_registration_id")
    if pre_registration_id:
        pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if pre_registration is not None:
            return build_pending_summary_from_pre_registration(pre_registration)

    person_id = session.get("pending_registration_person_id")
    if not person_id:
        return None
    try:
        person = Person.objects.select_related(
            "class_group__class_category", "person_type"
        ).get(pk=person_id)
    except Person.DoesNotExist:
        return None

    class_group_summary = build_person_class_group_summary(person)
    base = {
        "id": person.pk,
        "full_name": person.full_name,
        "email": person.email or "",
        "phone": person.phone or "",
        "class_group_name": class_group_summary["class_group_name"],
        "class_group_ids": class_group_summary["class_group_ids"],
        "person_type_code": person.person_type.code if person.person_type else "",
    }

    students = list(
        PersonRelationship.objects.filter(
            source_person=person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        ).select_related("target_person__class_group__class_category")
    )
    if students:
        base["students"] = [
            {
                "full_name": rel.target_person.full_name,
                **build_person_class_group_summary(rel.target_person),
            }
            for rel in students
        ]
    return base


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


def build_person_class_group_summary(person):
    if not person.class_group_id:
        return {"class_group_name": "", "class_group_ids": []}
    return build_class_group_summary_from_groups([person.class_group])


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
    """Prepara o snapshot do banco para uso como `data` no PortalRegistrationForm.

    Corrige dois problemas acumulados em snapshots antigos:
    - MultipleChoiceField (class_groups) salvo como string quando havia apenas 1 valor → converte para lista.
    - Campos scalar salvos como lista por duplicata de input no template → toma o primeiro valor.
    - Entradas de dicionário aninhado (plan_payment, etc.) não são campos do form → removidas.
    """
    result = {}
    for key, value in snapshot.items():
        if isinstance(value, dict):
            continue  # plan_payment, materials_payment — não são campos do form
        if key in MULTI_VALUE_FORM_FIELDS:
            # Garante que MultipleChoiceField sempre receba lista
            if isinstance(value, list):
                result[key] = value
            elif value:
                result[key] = [value]
            else:
                result[key] = []
        elif isinstance(value, list):
            # Campo scalar armazenado como lista por bug de duplicata — usa primeiro valor
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
    """
    Finaliza um PreRegistration: cria Person/PortalAccount via form, ativa contas,
    sincroniza pagamento já confirmado e concede aula experimental se aplicável.

    Retorna um dict com chaves:
        - "ok": bool
        - "error": str | None
        - "person": Person | None
        - "portal_account": PortalAccount | None
        - "already_finalized": bool
    """
    from system.forms import PortalRegistrationForm
    from system.models.registration_order import PaymentStatus

    if pre_registration.status == PreRegistrationStatus.FINALIZED and pre_registration.finalized_person:
        return {
            "ok": True,
            "error": None,
            "person": pre_registration.finalized_person,
            "portal_account": getattr(pre_registration.finalized_person, "access_account", None),
            "already_finalized": True,
        }

    form_data = normalize_snapshot_for_form(pre_registration.form_snapshot or {})
    form = PortalRegistrationForm(data=form_data)
    if not form.is_valid():
        return {
            "ok": False,
            "error": "Revise os dados do cadastro antes de finalizar.",
            "person": None,
            "portal_account": None,
            "already_finalized": False,
        }

    created_people = form.save()
    primary_person = (
        created_people.get("holder")
        or created_people.get("guardian")
        or created_people.get("other")
    )
    if primary_person is None:
        return {
            "ok": False,
            "error": "Não foi possível finalizar o cadastro.",
            "person": None,
            "portal_account": None,
            "already_finalized": False,
        }

    if not primary_person.is_active:
        primary_person.is_active = True
        primary_person.save(update_fields=["is_active", "updated_at"])
    portal_account = getattr(primary_person, "access_account", None)
    if portal_account and not portal_account.is_active:
        portal_account.is_active = True
        portal_account.save(update_fields=["is_active", "updated_at"])

    pre_registration.mark_finalized(primary_person)

    # Sincroniza o pagamento já realizado no Asaas/Stripe com a RegistrationOrder criada pela finalização.
    # form.save() → create_portal_registration() → create_registration_order() cria uma ordem PENDING para
    # a pessoa recém-criada. Quando o pré-cadastro já teve pagamento confirmado (plan_paid=True no snapshot),
    # essa ordem deve ser marcada como PAID para não bloquear o login do usuário.
    snapshot = pre_registration.form_snapshot or {}
    order = created_people.get("order")
    if order is not None and snapshot.get("plan_paid") and order.payment_status == PaymentStatus.PENDING:
        plan_payment = snapshot.get("plan_payment") or {}
        asaas_payment_id = plan_payment.get("asaas_payment_id") or ""
        order.payment_status = PaymentStatus.PAID
        order.paid_at = timezone.now()
        if asaas_payment_id:
            order.asaas_payment_id = asaas_payment_id
        order.save(update_fields=["payment_status", "paid_at", "asaas_payment_id", "updated_at"])
        from system.services.membership import activate_membership_from_paid_order
        activate_membership_from_paid_order(
            order,
            notes="Pagamento confirmado via pré-cadastro.",
        )

    # Aula experimental: criar RegistrationOrder pendente e TrialAccessGrant
    if snapshot.get("trial_requested"):
        grant_trial_for_pre_registration(pre_registration, primary_person)

    return {
        "ok": True,
        "error": None,
        "person": primary_person,
        "portal_account": portal_account,
        "already_finalized": False,
    }
