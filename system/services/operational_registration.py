import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_time

from system.constants import PersonTypeCode
from system.models import (
    AdministrativeAccessRequest,
    AdministrativeAccessRequestOrigin,
    ClassCatalogRequest,
    ClassCategory,
)
from system.services.access_requests import create_administrative_access_request
from system.services.class_requests import create_new_teacher_class_request


@transaction.atomic
def submit_operational_pre_registration(pre_registration, cleaned_data):
    existing_submission = (pre_registration.form_snapshot or {}).get(
        "operational_submission"
    )
    if existing_submission:
        return _get_existing_submission(existing_submission)

    type_code = cleaned_data.get("other_type_code") or ""
    if type_code == PersonTypeCode.ADMINISTRATIVE_ASSISTANT:
        submission = _create_administrative_request(cleaned_data)
        kind = "administrative_access"
    elif type_code == PersonTypeCode.INSTRUCTOR:
        submission = _create_teacher_request(cleaned_data)
        kind = "class_catalog"
    else:
        raise ValidationError("Perfil operacional inválido.")

    snapshot = dict(pre_registration.form_snapshot or {})
    snapshot["operational_submission"] = {
        "kind": kind,
        "request_id": submission.pk,
    }
    pre_registration.form_snapshot = snapshot
    pre_registration.mark_finalized(None)
    return submission


def _create_administrative_request(cleaned_data):
    try:
        role_codes = json.loads(
            cleaned_data.get("operational_requested_roles_payload") or "[]"
        )
    except json.JSONDecodeError as error:
        raise ValidationError("Selecione áreas administrativas válidas.") from error

    notes = (cleaned_data.get("operational_compensation_notes") or "").strip()
    return create_administrative_access_request(
        origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
        full_name=cleaned_data.get("other_name", ""),
        cpf=cleaned_data.get("other_cpf", ""),
        email=cleaned_data.get("other_email", ""),
        phone=cleaned_data.get("other_phone", ""),
        requested_role_codes=role_codes,
        justification=notes or "Solicitação enviada pelo cadastro público.",
        password=cleaned_data.get("other_password", ""),
        request_payload={
            "training_intent": cleaned_data.get("operational_training_intent") or "none",
            "compensation_preference": (
                cleaned_data.get("operational_compensation_preference") or "none"
            ),
            "pix_key_type": cleaned_data.get("operational_pix_key_type") or "",
            "pix_key": cleaned_data.get("operational_pix_key") or "",
        },
    )


def _create_teacher_request(cleaned_data):
    if cleaned_data.get("teacher_assignment_mode") != "propose":
        raise ValidationError(
            "Para o cadastro público de professor, crie uma proposta de horário."
        )

    try:
        schedule = json.loads(cleaned_data.get("teacher_proposed_schedule_payload") or "{}")
    except json.JSONDecodeError as error:
        raise ValidationError("Informe uma proposta de horário válida.") from error

    category = ClassCategory.objects.filter(
        pk=schedule.get("category_id"), is_active=True
    ).first()
    if category is None:
        raise ValidationError("Selecione uma categoria de turma ativa.")

    weekdays = schedule.get("weekdays") or []
    start_time = parse_time(schedule.get("start_time") or "")
    if not weekdays or start_time is None:
        raise ValidationError("Informe dias e horário de início válidos.")

    duration_minutes = _positive_int(schedule.get("duration_minutes"), default=60)
    default_capacity = _positive_int(schedule.get("default_capacity"), default=0)
    training_style = schedule.get("training_style") or "mixed"
    extra_schedules = [
        {
            "weekday": weekday,
            "training_style": training_style,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
        }
        for weekday in weekdays[1:]
    ]
    payout_method = cleaned_data.get("operational_payout_method") or "none"
    if payout_method == "bank":
        payout_method = "bank_account"

    return create_new_teacher_class_request(
        full_name=cleaned_data.get("other_name", ""),
        cpf=cleaned_data.get("other_cpf", ""),
        email=cleaned_data.get("other_email", ""),
        phone=cleaned_data.get("other_phone", ""),
        password=cleaned_data.get("other_password", ""),
        class_category=category,
        display_name=schedule.get("display_name") or "",
        weekday=weekdays[0],
        training_style=training_style,
        start_time=start_time,
        duration_minutes=duration_minutes,
        default_capacity=default_capacity,
        justification=(
            schedule.get("justification")
            or cleaned_data.get("operational_compensation_notes")
            or "Proposta enviada pelo cadastro público."
        ),
        martial_art=cleaned_data.get("other_martial_art", ""),
        martial_art_graduation=cleaned_data.get("other_martial_art_graduation", ""),
        jiu_jitsu_belt=cleaned_data.get("other_jiu_jitsu_belt", ""),
        jiu_jitsu_stripes=cleaned_data.get("other_jiu_jitsu_stripes"),
        extra_schedules=extra_schedules,
        payout_data={
            "method": payout_method,
            "pix_key_type": cleaned_data.get("operational_pix_key_type") or "",
            "pix_key": cleaned_data.get("operational_pix_key") or "",
            "bank_account_details": cleaned_data.get("operational_bank_details") or "",
            "holder_name": cleaned_data.get("other_name", ""),
            "holder_document": cleaned_data.get("other_cpf", ""),
            "financial_arrangement": (
                cleaned_data.get("operational_financial_arrangement") or ""
            ),
            "fixed_amount": cleaned_data.get("operational_fixed_amount") or "",
            "student_percentage": (
                cleaned_data.get("operational_student_percentage") or ""
            ),
        },
    )


def _positive_int(value, *, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _get_existing_submission(submission):
    request_id = submission.get("request_id")
    if submission.get("kind") == "administrative_access":
        return AdministrativeAccessRequest.objects.get(pk=request_id)
    if submission.get("kind") == "class_catalog":
        return ClassCatalogRequest.objects.get(pk=request_id)
    raise ValidationError("Solicitação operacional inválida.")
