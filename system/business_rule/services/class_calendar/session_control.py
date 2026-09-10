from django.conf import settings
from django.db import transaction
from django.utils import timezone
from system.business_rule.constants import PersonTypeCode
from system.business_rule.services.class_calendar.authorization import assert_instructor_owns_schedule, assert_instructor_owns_special
from system.business_rule.services.class_calendar.state import session_creation_defaults, session_is_confirmed, special_is_confirmed
from system.business_rule.models import ClassSchedule, ClassSession, Person, SpecialClass
from system.business_rule.models.calendar import SessionStatus


@transaction.atomic
def assign_session_substitute(instructor, schedule_id, substitute_teacher_id):
    today = timezone.localdate()
    schedule = assert_instructor_owns_schedule(instructor, schedule_id)
    session = (
        ClassSession.objects.filter(schedule=schedule, date=today)
        .select_related("substitute_teacher")
        .first()
    )
    if session_is_confirmed(session):
        raise ValueError("Cancele sua confirmação antes de indicar um substituto.")

    if session is None:
        session = ClassSession.objects.create(
            schedule=schedule,
            date=today,
            status=SessionStatus.SCHEDULED,
            instructor_present=False,
        )
    elif session.is_cancelled:
        raise ValueError("Esta aula foi cancelada.")

    substitute = (
        Person.objects.select_related("person_type")
        .filter(
            pk=substitute_teacher_id,
            is_active=True,
            person_type__code=PersonTypeCode.INSTRUCTOR,
        )
        .first()
    )
    if substitute is None:
        raise ValueError("Professor substituto inválido.")
    if substitute.pk == instructor.pk:
        raise ValueError("Escolha outro professor para a substituição.")

    session.substitute_teacher = substitute
    session.instructor_present = False
    session.instructor_checked_in_at = None
    session.save(
        update_fields=[
            "substitute_teacher",
            "instructor_present",
            "instructor_checked_in_at",
            "updated_at",
        ]
    )
    return session


@transaction.atomic
def assign_special_substitute(instructor, special_id, substitute_teacher_id):
    special = assert_instructor_owns_special(instructor, special_id)
    today = timezone.localdate()
    if special.date != today:
        raise ValueError("Indicação de substituto só é permitida no dia do aulão.")
    if special_is_confirmed(special):
        raise ValueError("Cancele sua confirmação antes de indicar um substituto.")
    if special.is_cancelled:
        raise ValueError("Este aulão foi cancelado.")

    substitute = (
        Person.objects.select_related("person_type")
        .filter(
            pk=substitute_teacher_id,
            is_active=True,
            person_type__code=PersonTypeCode.INSTRUCTOR,
        )
        .first()
    )
    if substitute is None:
        raise ValueError("Professor substituto inválido.")
    if substitute.pk == instructor.pk:
        raise ValueError("Escolha outro professor para a substituição.")

    special.substitute_teacher = substitute
    special.instructor_present = False
    special.instructor_checked_in_at = None
    special.save(
        update_fields=[
            "substitute_teacher",
            "instructor_present",
            "instructor_checked_in_at",
            "updated_at",
        ]
    )
    return special


@transaction.atomic
def cancel_class_without_instructor(instructor, schedule_id, reason="Sem professor disponível"):
    today = timezone.localdate()
    schedule = assert_instructor_owns_schedule(instructor, schedule_id)
    session = ClassSession.objects.filter(schedule=schedule, date=today).first()
    if session and not session.is_cancelled and session.instructor_present:
        raise ValueError("Cancele a confirmação antes de cancelar a aula.")
    if session and not session.is_cancelled and session.substitute_teacher_id:
        raise ValueError("Há um substituto indicado para esta aula.")
    return toggle_session_cancel(schedule_id, today, reason)


@transaction.atomic
def toggle_special_cancel(special_id, reason=""):
    special = SpecialClass.objects.get(pk=special_id)
    if special.is_cancelled:
        special.status = SessionStatus.SCHEDULED
        special.cancellation_reason = ""
    else:
        special.status = SessionStatus.CANCELLED
        special.cancellation_reason = reason
    special.save(update_fields=["status", "cancellation_reason", "updated_at"])
    return special


@transaction.atomic
def cancel_special_without_instructor(instructor, special_id, reason="Sem professor disponível"):
    today = timezone.localdate()
    special = assert_instructor_owns_special(instructor, special_id)
    if special.date != today:
        raise ValueError("Cancelamento só é permitido no dia do aulão.")
    if special.instructor_present:
        raise ValueError("Cancele a confirmação antes de cancelar o aulão.")
    if special.substitute_teacher_id:
        raise ValueError("Há um substituto indicado para este aulão.")
    return toggle_special_cancel(special_id, reason)


@transaction.atomic
def toggle_session_cancel(schedule_id, session_date, reason=""):
    schedule = ClassSchedule.objects.get(pk=schedule_id)
    session, created = ClassSession.objects.get_or_create(
        schedule=schedule,
        date=session_date,
        defaults=session_creation_defaults(),
    )
    if session.is_cancelled:
        session.status = SessionStatus.SCHEDULED
        session.cancellation_reason = ""
    else:
        session.status = SessionStatus.CANCELLED
        session.cancellation_reason = reason
    session.save()
    return session


@transaction.atomic
def create_special_class(
    *,
    title,
    session_date,
    start_time,
    duration_minutes=None,
    teacher=None,
    notes="",
):
    if not title:
        title = settings.SPECIAL_CLASS_DEFAULT_TITLE
    now = timezone.now()
    special = SpecialClass.objects.create(
        title=title,
        date=session_date,
        start_time=start_time,
        duration_minutes=duration_minutes or settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES,
        teacher=teacher,
        notes=notes or "",
        instructor_present=True,
        instructor_checked_in_at=now,
    )
    return special


@transaction.atomic
def delete_special_class(special_id):
    SpecialClass.objects.filter(pk=special_id).delete()
