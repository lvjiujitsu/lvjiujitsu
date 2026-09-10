from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from system.business_rule.constants import PersonTypeCode
from system.business_rule.models import (
    ClassCatalogRequest,
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
from system.business_rule.services.class_requests.payload import deserialize_extra_schedules, payload_to_json, resolve_approved_payload
from system.business_rule.services.class_requests.validation import require_pending, validate_schedule_slot_available


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
    require_pending(catalog_request)
    approved = resolve_approved_payload(
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
    catalog_request.approved_payload = payload_to_json(approved)
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
    require_pending(catalog_request)
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
    require_pending(catalog_request)
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


def _approve_new_schedule(catalog_request, approved):
    class_group = approved["class_group"]
    validate_schedule_slot_available(
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
    for index, extra in enumerate(deserialize_extra_schedules(catalog_request.extra_schedules), start=1):
        validate_schedule_slot_available(
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
