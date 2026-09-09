import json
import uuid

from datetime import time

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from system.business_rule.constants import PersonTypeCode, Capability
from system.business_rule.models import (
    ClassCatalogRequest,
    ClassCatalogRequestOrigin,
    ClassCatalogRequestStatus,
    ClassCatalogRequestType,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    PortalAccount,
    TeacherBankAccount,
)
from system.business_rule.services.registration import ensure_default_person_types
from system.business_rule.services.class_overview import resolve_class_group_selection
from system.core.documents import ensure_formatted_cpf


def create_existing_teacher_class_request(
    *,
    requester,
    request_type,
    class_group,
    class_category,
    display_name,
    weekday,
    training_style,
    start_time,
    duration_minutes,
    default_capacity,
    justification,
    extra_schedules=None,
):
    if request_type == ClassCatalogRequestType.NEW_SCHEDULE:
        _validate_scoped_class_group(requester, class_group)
        _validate_schedule_slot_available(
            class_group=class_group,
            weekday=weekday,
            training_style=training_style,
            start_time=start_time,
        )
        if extra_schedules:
            raise ValidationError("Horários adicionais só se aplicam à criação de nova turma.")
    elif request_type == ClassCatalogRequestType.NEW_CLASS_GROUP:
        if class_category is None:
            raise ValidationError("Selecione a categoria da nova turma.")
        if not (display_name or "").strip():
            raise ValidationError("Informe o nome da nova turma.")
    else:
        raise ValidationError("Tipo de solicitação inválido para professor logado.")

    _validate_schedule_payload(weekday, training_style, start_time, duration_minutes)
    normalized_extra_schedules = _normalize_extra_schedules(
        extra_schedules, primary_slot=(weekday, training_style, start_time)
    )
    request = ClassCatalogRequest.objects.create(
        origin=ClassCatalogRequestOrigin.PORTAL,
        status=ClassCatalogRequestStatus.PENDING,
        request_type=request_type,
        requester_person=requester,
        teacher_person=requester,
        target_class_group=class_group if request_type == ClassCatalogRequestType.NEW_SCHEDULE else None,
        class_category=class_category,
        display_name=(display_name or "").strip(),
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
        duration_minutes=duration_minutes,
        default_capacity=default_capacity or 0,
        justification=(justification or "").strip(),
        extra_schedules=_serialize_extra_schedules(normalized_extra_schedules),
    )
    request.payload = _build_payload(request)
    request.save(update_fields=("payload", "updated_at"))
    return request


def create_new_teacher_class_request(
    *,
    full_name,
    cpf,
    email,
    phone,
    password,
    class_category,
    display_name,
    weekday,
    training_style,
    start_time,
    duration_minutes,
    default_capacity,
    justification,
    martial_art="",
    martial_art_graduation="",
    jiu_jitsu_belt="",
    jiu_jitsu_stripes=None,
    extra_schedules=None,
    payout_data=None,
):
    formatted_cpf = ensure_formatted_cpf(cpf)
    if _has_pending_new_teacher_request(formatted_cpf):
        raise ValidationError("Já existe uma proposta pendente para este CPF.")
    if class_category is None:
        raise ValidationError("Selecione a categoria da turma proposta.")
    if not (display_name or "").strip():
        raise ValidationError("Informe o nome da turma proposta.")
    if not password:
        raise ValidationError("Informe uma senha inicial para o professor.")
    _validate_schedule_payload(weekday, training_style, start_time, duration_minutes)
    normalized_extra_schedules = _normalize_extra_schedules(
        extra_schedules, primary_slot=(weekday, training_style, start_time)
    )

    request = ClassCatalogRequest.objects.create(
        origin=ClassCatalogRequestOrigin.PUBLIC_REGISTRATION,
        status=ClassCatalogRequestStatus.PENDING,
        request_type=ClassCatalogRequestType.NEW_TEACHER_WITH_SCHEDULE,
        full_name=(full_name or "").strip(),
        cpf=formatted_cpf,
        email=(email or "").strip(),
        phone=(phone or "").strip(),
        password_hash=make_password(password),
        martial_art=martial_art or "",
        martial_art_graduation=martial_art_graduation or "",
        jiu_jitsu_belt=jiu_jitsu_belt or "",
        jiu_jitsu_stripes=jiu_jitsu_stripes,
        class_category=class_category,
        display_name=(display_name or "").strip(),
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
        duration_minutes=duration_minutes,
        default_capacity=default_capacity or 0,
        justification=(justification or "").strip(),
        extra_schedules=_serialize_extra_schedules(normalized_extra_schedules),
    )
    request.payload = _build_payload(request, payout_data=payout_data)
    request.save(update_fields=("payload", "updated_at"))
    return request


def create_public_teacher_join_requests(
    *,
    full_name,
    cpf,
    email,
    phone,
    password,
    class_groups_payload,
    justification="",
    martial_art="",
    martial_art_graduation="",
    jiu_jitsu_belt="",
    jiu_jitsu_stripes=None,
    payout_data=None,
):
    formatted_cpf = ensure_formatted_cpf(cpf)
    if not password:
        raise ValidationError("Informe uma senha inicial para o professor.")
    if isinstance(class_groups_payload, str):
        try:
            selection_items = json.loads(class_groups_payload or "[]")
        except json.JSONDecodeError as error:
            raise ValidationError("Selecione turmas ativas válidas.") from error
    else:
        selection_items = class_groups_payload or []

    raw_values = []
    for item in selection_items:
        if isinstance(item, dict):
            raw_values.append(str(item.get("id") or item.get("class_group_id") or ""))
        else:
            raw_values.append(str(item))
    raw_values = [value for value in raw_values if value]

    class_groups = resolve_class_group_selection(raw_values)
    if not class_groups:
        raise ValidationError("Selecione ao menos uma turma ativa.")

    submission_batch_id = uuid.uuid4().hex
    created_requests = []
    for class_group in class_groups:
        if _has_pending_join_request(formatted_cpf, class_group.pk):
            raise ValidationError(
                f"Já existe uma solicitação pendente para a turma {class_group.display_name}."
            )
        current_teacher = class_group.main_teacher
        current_teacher_id = getattr(current_teacher, "pk", None)
        requested_role = "assistant" if current_teacher_id else "primary"
        request = ClassCatalogRequest.objects.create(
            origin=ClassCatalogRequestOrigin.PUBLIC_REGISTRATION,
            status=ClassCatalogRequestStatus.PENDING,
            request_type=ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS,
            target_class_group=class_group,
            class_category=class_group.class_category,
            display_name=class_group.display_name,
            full_name=(full_name or "").strip(),
            cpf=formatted_cpf,
            email=(email or "").strip(),
            phone=(phone or "").strip(),
            password_hash=make_password(password),
            martial_art=martial_art or "",
            martial_art_graduation=martial_art_graduation or "",
            jiu_jitsu_belt=jiu_jitsu_belt or "",
            jiu_jitsu_stripes=jiu_jitsu_stripes,
            justification=(
                (justification or "").strip()
                or "Solicitação de vínculo enviada pelo cadastro público."
            ),
        )
        payload = _payload_to_json(
            {
                "class_group": class_group,
                "class_category": class_group.class_category,
                "display_name": class_group.display_name,
            }
        )
        payload["requested_role"] = requested_role
        payload["approval_scope"] = (
            "admin_and_current_teacher" if current_teacher_id else "admin_only"
        )
        payload["current_teacher_id"] = current_teacher_id
        payload["current_teacher_name"] = (
            current_teacher.full_name if current_teacher is not None else ""
        )
        payload["submission_batch_id"] = submission_batch_id
        if payout_data is not None:
            payload["payout"] = _normalize_payout_payload(payout_data)
        request.payload = payload
        request.save(update_fields=("payload", "updated_at"))
        created_requests.append(request)
    return created_requests


@transaction.atomic
def approve_class_catalog_request(
    request_id,
    *,
    approved_by,
    class_group=None,
    class_category=None,
    display_name=None,
    weekday=None,
    training_style=None,
    start_time=None,
    duration_minutes=None,
    default_capacity=None,
    decision_notes="",
):
    catalog_request = (
        ClassCatalogRequest.objects.select_for_update()
        .select_related(
            "requester_person",
            "teacher_person",
            "target_class_group",
            "class_category",
        )
        .get(pk=request_id)
    )
    _require_pending(catalog_request)
    approved = _resolve_approved_payload(
        catalog_request,
        class_group=class_group,
        class_category=class_category,
        display_name=display_name,
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
        duration_minutes=duration_minutes,
        default_capacity=default_capacity,
    )

    if catalog_request.request_type == ClassCatalogRequestType.NEW_SCHEDULE:
        created_group = _approve_new_schedule(catalog_request, approved)
        created_teacher = None
    elif catalog_request.request_type == ClassCatalogRequestType.NEW_CLASS_GROUP:
        created_teacher = catalog_request.teacher_person
        created_group = _approve_new_class_group(catalog_request, approved, created_teacher)
    elif catalog_request.request_type == ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS:
        created_teacher = _resolve_or_create_instructor(catalog_request)
        created_group = _approve_teacher_join_existing(
            catalog_request,
            approved,
            created_teacher,
        )
    else:
        created_teacher = _resolve_or_create_instructor(catalog_request)
        created_group = _approve_new_class_group(catalog_request, approved, created_teacher)

    catalog_request.status = ClassCatalogRequestStatus.APPROVED
    catalog_request.created_teacher = created_teacher
    catalog_request.created_class_group = created_group
    catalog_request.decided_by = approved_by
    catalog_request.decided_at = timezone.now()
    catalog_request.decision_notes = (decision_notes or "").strip()
    catalog_request.approved_payload = _payload_to_json(approved)
    catalog_request.save(
        update_fields=(
            "status",
            "created_teacher",
            "created_class_group",
            "decided_by",
            "decided_at",
            "decision_notes",
            "approved_payload",
            "updated_at",
        )
    )
    return catalog_request


@transaction.atomic
def reject_class_catalog_request(request_id, *, rejected_by, decision_notes):
    catalog_request = ClassCatalogRequest.objects.select_for_update().get(pk=request_id)
    _require_pending(catalog_request)
    if not (decision_notes or "").strip():
        raise ValidationError("Informe o motivo da recusa.")
    catalog_request.status = ClassCatalogRequestStatus.REJECTED
    catalog_request.decided_by = rejected_by
    catalog_request.decided_at = timezone.now()
    catalog_request.decision_notes = decision_notes.strip()
    catalog_request.save(
        update_fields=(
            "status",
            "decided_by",
            "decided_at",
            "decision_notes",
            "updated_at",
        )
    )
    return catalog_request


@transaction.atomic
def cancel_class_catalog_request(request_id, *, canceled_by, decision_notes=""):
    catalog_request = ClassCatalogRequest.objects.select_for_update().get(pk=request_id)
    _require_pending(catalog_request)
    catalog_request.status = ClassCatalogRequestStatus.CANCELED
    catalog_request.decided_by = canceled_by
    catalog_request.decided_at = timezone.now()
    catalog_request.decision_notes = (decision_notes or "Cancelada pelo solicitante.").strip()
    catalog_request.save(
        update_fields=(
            "status",
            "decided_by",
            "decided_at",
            "decision_notes",
            "updated_at",
        )
    )
    return catalog_request


CLASS_CATALOG_DECISION_CAPABILITIES = (
    Capability.MANAGE_CLASSES,
    Capability.MANAGE_ACADEMY,
)


def can_decide_class_catalog_request(request_capabilities):
    return bool(set(CLASS_CATALOG_DECISION_CAPABILITIES) & set(request_capabilities))


def can_cancel_class_catalog_request(catalog_request, *, actor, actor_capabilities):
    if can_decide_class_catalog_request(actor_capabilities):
        return True
    if actor is None:
        return False
    return actor.pk in (catalog_request.requester_person_id, catalog_request.teacher_person_id)


def get_class_catalog_requests_for_person(person, limit=5):
    if person is None:
        return []
    return list(
        ClassCatalogRequest.objects.filter(
            requester_person=person,
        )
        .select_related("target_class_group", "created_class_group")
        .order_by("-created_at")[:limit]
    )


def get_class_catalog_requests_history_for_person(person, limit=20):
    if person is None:
        return []
    return list(
        ClassCatalogRequest.objects.filter(
            Q(requester_person=person) | Q(teacher_person=person) | Q(created_teacher=person)
        )
        .select_related("target_class_group", "created_class_group")
        .order_by("-created_at")
        .distinct()[:limit]
    )


def get_pending_class_catalog_request_count():
    return ClassCatalogRequest.objects.filter(
        status=ClassCatalogRequestStatus.PENDING,
    ).count()


def _approve_new_schedule(catalog_request, approved):
    class_group = approved["class_group"]
    _validate_schedule_slot_available(
        class_group=class_group,
        weekday=approved["weekday"],
        training_style=approved["training_style"],
        start_time=approved["start_time"],
        exclude_request_id=catalog_request.pk,
    )
    ClassSchedule.objects.create(
        class_group=class_group,
        weekday=approved["weekday"],
        training_style=approved["training_style"],
        start_time=approved["start_time"],
        duration_minutes=approved["duration_minutes"],
        display_order=0,
        is_active=True,
    )
    return class_group


def _approve_new_class_group(catalog_request, approved, teacher):
    if teacher is None:
        raise ValidationError("A solicitação não possui professor aprovado.")
    class_group = ClassGroup.objects.create(
        display_name=approved["display_name"],
        class_category=approved["class_category"],
        main_teacher=teacher,
        default_capacity=approved["default_capacity"],
        is_active=True,
    )
    ClassSchedule.objects.create(
        class_group=class_group,
        weekday=approved["weekday"],
        training_style=approved["training_style"],
        start_time=approved["start_time"],
        duration_minutes=approved["duration_minutes"],
        display_order=0,
        is_active=True,
    )
    for index, extra in enumerate(_deserialize_extra_schedules(catalog_request.extra_schedules), start=1):
        _validate_schedule_slot_available(
            class_group=class_group,
            weekday=extra["weekday"],
            training_style=extra["training_style"],
            start_time=extra["start_time"],
        )
        ClassSchedule.objects.create(
            class_group=class_group,
            weekday=extra["weekday"],
            training_style=extra["training_style"],
            start_time=extra["start_time"],
            duration_minutes=extra["duration_minutes"],
            display_order=index,
            is_active=True,
        )
    return class_group


def _approve_teacher_join_existing(catalog_request, approved, teacher):
    class_group = approved["class_group"]
    if class_group is None:
        raise ValidationError("Selecione a turma de vínculo.")
    locked_group = (
        ClassGroup.objects.select_for_update()
        .select_related("main_teacher")
        .get(pk=class_group.pk)
    )
    if not locked_group.is_active:
        raise ValidationError("A turma selecionada não está mais ativa.")
    requested_role = (catalog_request.payload or {}).get("requested_role") or "assistant"
    if requested_role == "primary" or locked_group.main_teacher_id is None:
        if (
            locked_group.main_teacher_id
            and locked_group.main_teacher_id != teacher.pk
        ):
            raise ValidationError(
                "A turma já possui professor principal. Aprove como assistente ou recuse."
            )
        locked_group.main_teacher = teacher
        locked_group.save(update_fields=("main_teacher", "updated_at"))
        return locked_group
    ClassInstructorAssignment.objects.update_or_create(
        class_group=locked_group,
        person=teacher,
        defaults={"is_primary": False},
    )
    return locked_group


def _resolve_or_create_instructor(catalog_request):
    person_types = ensure_default_person_types()
    instructor_type = person_types[PersonTypeCode.INSTRUCTOR]
    person = Person.objects.filter(cpf=catalog_request.cpf).first()
    if person is None:
        person = Person.objects.create(
            full_name=catalog_request.full_name,
            cpf=catalog_request.cpf,
            email=catalog_request.email,
            phone=catalog_request.phone,
            person_type=instructor_type,
            martial_art=catalog_request.martial_art,
            martial_art_graduation=catalog_request.martial_art_graduation,
            jiu_jitsu_belt=catalog_request.jiu_jitsu_belt,
            jiu_jitsu_stripes=catalog_request.jiu_jitsu_stripes,
            is_active=True,
        )
    else:
        person.person_type = instructor_type
        person.is_active = True
        for field_name in ("email", "phone"):
            if not getattr(person, field_name) and getattr(catalog_request, field_name):
                setattr(person, field_name, getattr(catalog_request, field_name))
        person.save(update_fields=("person_type", "is_active", "email", "phone", "updated_at"))
    _ensure_portal_account(person, catalog_request.password_hash)
    _sync_teacher_bank_account(person, catalog_request.payload.get("payout") or {})
    return person


def _ensure_portal_account(person, password_hash):
    account = getattr(person, "access_account", None)
    if account is not None:
        if not account.is_active:
            account.is_active = True
            account.save(update_fields=("is_active", "updated_at"))
        return account
    return PortalAccount.objects.create(
        person=person,
        password_hash=password_hash or make_password(None),
        is_active=True,
    )


def _resolve_approved_payload(
    catalog_request,
    *,
    class_group,
    class_category,
    display_name,
    weekday,
    training_style,
    start_time,
    duration_minutes,
    default_capacity,
):
    resolved_group = class_group or catalog_request.target_class_group
    resolved_category = class_category or catalog_request.class_category
    resolved_display_name = (display_name if display_name is not None else catalog_request.display_name).strip()
    resolved_weekday = weekday or catalog_request.weekday
    resolved_training_style = training_style or catalog_request.training_style
    resolved_start_time = start_time or catalog_request.start_time
    resolved_duration = duration_minutes or catalog_request.duration_minutes
    resolved_capacity = default_capacity if default_capacity is not None else catalog_request.default_capacity

    if catalog_request.request_type == ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS:
        resolved_group = class_group or catalog_request.target_class_group
        if resolved_group is None:
            raise ValidationError("Selecione a turma de vínculo.")
        if not resolved_group.is_active:
            raise ValidationError("A turma selecionada não está mais ativa.")
        return {"class_group": resolved_group}

    if catalog_request.request_type == ClassCatalogRequestType.NEW_SCHEDULE and resolved_group is None:
        raise ValidationError("Selecione a turma que receberá o novo horário.")
    if catalog_request.request_type != ClassCatalogRequestType.NEW_SCHEDULE:
        if resolved_category is None:
            raise ValidationError("Selecione a categoria da nova turma.")
        if not resolved_display_name:
            raise ValidationError("Informe o nome da nova turma.")
    _validate_schedule_payload(
        resolved_weekday,
        resolved_training_style,
        resolved_start_time,
        resolved_duration,
    )
    return {
        "class_group": resolved_group,
        "class_category": resolved_category,
        "display_name": resolved_display_name,
        "weekday": resolved_weekday,
        "training_style": resolved_training_style,
        "start_time": resolved_start_time,
        "duration_minutes": resolved_duration,
        "default_capacity": resolved_capacity or 0,
    }


def _validate_scoped_class_group(person, class_group):
    if class_group is None:
        raise ValidationError("Selecione a turma existente.")
    if class_group.main_teacher_id == person.pk:
        return
    if ClassInstructorAssignment.objects.filter(class_group=class_group, person=person).exists():
        return
    raise ValidationError("Professor pode solicitar horário apenas para turma em que atua.")


def _validate_schedule_payload(weekday, training_style, start_time, duration_minutes):
    if not weekday:
        raise ValidationError("Informe o dia da semana.")
    if not training_style:
        raise ValidationError("Informe o estilo de treino.")
    if start_time is None:
        raise ValidationError("Informe o horário de início.")
    if not duration_minutes or int(duration_minutes) <= 0:
        raise ValidationError("Informe uma duração válida.")


def _validate_schedule_slot_available(
    *,
    class_group,
    weekday,
    training_style,
    start_time,
    exclude_request_id=None,
):
    if ClassSchedule.objects.filter(
        class_group=class_group,
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
    ).exists():
        raise ValidationError("Já existe horário igual para esta turma.")
    pending_queryset = ClassCatalogRequest.objects.filter(
        status=ClassCatalogRequestStatus.PENDING,
        target_class_group=class_group,
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
    )
    if exclude_request_id is not None:
        pending_queryset = pending_queryset.exclude(pk=exclude_request_id)
    if pending_queryset.exists():
        raise ValidationError("Já existe solicitação pendente para este horário.")


MAX_EXTRA_SCHEDULES = 4


def _normalize_extra_schedules(extra_schedules, *, primary_slot):
    if not extra_schedules:
        return []
    if len(extra_schedules) > MAX_EXTRA_SCHEDULES:
        raise ValidationError(
            f"São permitidos no máximo {MAX_EXTRA_SCHEDULES} horários adicionais por solicitação."
        )
    seen_slots = {primary_slot}
    normalized = []
    for extra in extra_schedules:
        weekday = extra.get("weekday")
        training_style = extra.get("training_style")
        start_time = extra.get("start_time")
        duration_minutes = extra.get("duration_minutes")
        _validate_schedule_payload(weekday, training_style, start_time, duration_minutes)
        slot = (weekday, training_style, start_time)
        if slot in seen_slots:
            raise ValidationError("Horários adicionais não podem repetir dia, estilo e horário.")
        seen_slots.add(slot)
        normalized.append(
            {
                "weekday": weekday,
                "training_style": training_style,
                "start_time": start_time,
                "duration_minutes": int(duration_minutes),
            }
        )
    return normalized


def _serialize_extra_schedules(normalized_extra_schedules):
    return [
        {
            "weekday": extra["weekday"],
            "training_style": extra["training_style"],
            "start_time": extra["start_time"].strftime("%H:%M"),
            "duration_minutes": extra["duration_minutes"],
        }
        for extra in normalized_extra_schedules
    ]


def _deserialize_extra_schedules(stored_extra_schedules):
    deserialized = []
    for extra in stored_extra_schedules or []:
        deserialized.append(
            {
                "weekday": extra["weekday"],
                "training_style": extra["training_style"],
                "start_time": time.fromisoformat(extra["start_time"]),
                "duration_minutes": extra["duration_minutes"],
            }
        )
    return deserialized


def _has_pending_new_teacher_request(cpf):
    return ClassCatalogRequest.objects.filter(
        request_type__in=(
            ClassCatalogRequestType.NEW_TEACHER_WITH_SCHEDULE,
            ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS,
        ),
        status=ClassCatalogRequestStatus.PENDING,
        cpf=cpf,
    ).exists()


def _has_pending_join_request(cpf, class_group_id):
    return ClassCatalogRequest.objects.filter(
        request_type=ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS,
        status=ClassCatalogRequestStatus.PENDING,
        cpf=cpf,
        target_class_group_id=class_group_id,
    ).exists()


def _require_pending(catalog_request):
    if catalog_request.status != ClassCatalogRequestStatus.PENDING:
        raise ValidationError("A solicitação já foi decidida.")


def _build_payload(catalog_request, *, payout_data=None):
    payload = {
        "class_group": catalog_request.target_class_group,
        "class_category": catalog_request.class_category,
        "display_name": catalog_request.display_name,
        "weekday": catalog_request.weekday,
        "training_style": catalog_request.training_style,
        "start_time": catalog_request.start_time,
        "duration_minutes": catalog_request.duration_minutes,
        "default_capacity": catalog_request.default_capacity,
    }
    if payout_data is not None:
        payload["payout"] = _normalize_payout_payload(payout_data)
    return _payload_to_json(payload)


def _payload_to_json(payload):
    class_group = payload.get("class_group")
    class_category = payload.get("class_category")
    start_time = payload.get("start_time")
    result = {
        "class_group_id": class_group.pk if class_group else None,
        "class_group_label": str(class_group) if class_group else "",
        "class_category_id": class_category.pk if class_category else None,
        "class_category_label": str(class_category) if class_category else "",
        "display_name": payload.get("display_name") or "",
        "weekday": payload.get("weekday") or "",
        "training_style": payload.get("training_style") or "",
        "start_time": start_time.strftime("%H:%M") if start_time else "",
        "duration_minutes": payload.get("duration_minutes") or 0,
        "default_capacity": payload.get("default_capacity") or 0,
    }
    if "payout" in payload:
        result["payout"] = payload.get("payout") or {}
    return result


def _normalize_payout_payload(payout_data):
    payout_data = payout_data or {}
    method = payout_data.get("method") or "none"
    if method not in {"none", "pix", "bank_account"}:
        method = "none"
    pix_key_type = (payout_data.get("pix_key_type") or "").strip()
    pix_key = (payout_data.get("pix_key") or "").strip()
    bank_account_details = (payout_data.get("bank_account_details") or "").strip()
    financial_arrangement = (payout_data.get("financial_arrangement") or "").strip()
    if financial_arrangement not in {
        "",
        "pays_monthly",
        "barter",
        "volunteer",
        "paid_fixed",
        "paid_per_student",
        "paid_mixed",
    }:
        raise ValidationError("Informe uma condição financeira válida para o professor.")
    if method == "pix" and (not pix_key_type or not pix_key):
        raise ValidationError("Informe tipo e chave PIX para recebimento do professor.")
    if method == "bank_account" and not bank_account_details:
        raise ValidationError("Informe os dados bancários para recebimento do professor.")
    return {
        "method": method,
        "pix_key_type": pix_key_type if method == "pix" else "",
        "pix_key": pix_key if method == "pix" else "",
        "bank_account_details": bank_account_details if method == "bank_account" else "",
        "holder_name": (payout_data.get("holder_name") or "").strip(),
        "holder_document": (payout_data.get("holder_document") or "").strip(),
        "financial_arrangement": financial_arrangement,
        "fixed_amount": (payout_data.get("fixed_amount") or "").strip(),
        "student_percentage": (payout_data.get("student_percentage") or "").strip(),
    }


def _sync_teacher_bank_account(person, payout):
    if not payout or payout.get("method") != "pix":
        return None
    pix_key = (payout.get("pix_key") or "").strip()
    pix_key_type = (payout.get("pix_key_type") or "").strip()
    if not pix_key or not pix_key_type:
        return None
    account, _ = TeacherBankAccount.objects.update_or_create(
        person=person,
        defaults={
            "pix_key": pix_key,
            "pix_key_type": pix_key_type,
            "holder_name": (payout.get("holder_name") or "").strip(),
            "holder_document": (payout.get("holder_document") or "").strip(),
            "is_active": True,
        },
    )
    return account
