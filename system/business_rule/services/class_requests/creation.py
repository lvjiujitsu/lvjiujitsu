import json
import uuid
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from system.business_rule.models import (
    ClassCatalogRequest,
    ClassCatalogRequestOrigin,
    ClassCatalogRequestStatus,
    ClassCatalogRequestType,
)
from system.business_rule.services.class_overview import resolve_class_group_selection
from system.core.documents import ensure_formatted_cpf
from system.business_rule.services.class_requests.payload import build_payload, normalize_extra_schedules, normalize_payout_payload, payload_to_json, serialize_extra_schedules
from system.business_rule.services.class_requests.validation import has_pending_join_request, has_pending_new_teacher_request, validate_schedule_payload, validate_schedule_slot_available, validate_scoped_class_group


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
        validate_scoped_class_group(requester, class_group)
        validate_schedule_slot_available(
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

    validate_schedule_payload(weekday, training_style, start_time, duration_minutes)
    normalized_extra_schedules = normalize_extra_schedules(
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
        extra_schedules=serialize_extra_schedules(normalized_extra_schedules),
    )
    request.payload = build_payload(request)
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
    if has_pending_new_teacher_request(formatted_cpf):
        raise ValidationError("Já existe uma proposta pendente para este CPF.")
    if class_category is None:
        raise ValidationError("Selecione a categoria da turma proposta.")
    if not (display_name or "").strip():
        raise ValidationError("Informe o nome da turma proposta.")
    if not password:
        raise ValidationError("Informe uma senha inicial para o professor.")
    validate_schedule_payload(weekday, training_style, start_time, duration_minutes)
    normalized_extra_schedules = normalize_extra_schedules(
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
        extra_schedules=serialize_extra_schedules(normalized_extra_schedules),
    )
    request.payload = build_payload(request, payout_data=payout_data)
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
        if has_pending_join_request(formatted_cpf, class_group.pk):
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
        payload = payload_to_json(
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
            payload["payout"] = normalize_payout_payload(payout_data)
        request.payload = payload
        request.save(update_fields=("payload", "updated_at"))
        created_requests.append(request)
    return created_requests
