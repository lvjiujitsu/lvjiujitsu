from datetime import time
from django.core.exceptions import ValidationError
from system.business_rule.models import ClassCatalogRequestType
from system.business_rule.services.class_requests.validation import validate_schedule_payload


def resolve_approved_payload(
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
    validate_schedule_payload(
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


MAX_EXTRA_SCHEDULES = 4


def normalize_extra_schedules(extra_schedules, *, primary_slot):
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
        validate_schedule_payload(weekday, training_style, start_time, duration_minutes)
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


def serialize_extra_schedules(normalized_extra_schedules):
    return [
        {
            "weekday": extra["weekday"],
            "training_style": extra["training_style"],
            "start_time": extra["start_time"].strftime("%H:%M"),
            "duration_minutes": extra["duration_minutes"],
        }
        for extra in normalized_extra_schedules
    ]


def deserialize_extra_schedules(stored_extra_schedules):
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


def build_payload(catalog_request, *, payout_data=None):
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
        payload["payout"] = normalize_payout_payload(payout_data)
    return payload_to_json(payload)


def payload_to_json(payload):
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


def normalize_payout_payload(payout_data):
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
