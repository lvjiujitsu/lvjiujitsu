from types import SimpleNamespace
from django.db import transaction
from django.utils import timezone
from system.business_rule.services.membership import get_active_membership
from system.business_rule.services.membership_resolution import resolve_current_pause
from system.business_rule.services.trial_access import consume_trial_for_person
from system.business_rule.services.class_calendar.authorization import get_instructor_class_group_ids
from system.business_rule.services.class_calendar.state import session_creation_defaults, training_class_group_ids
from system.business_rule.models import ClassSchedule, ClassSession, Holiday, SpecialClass
from system.business_rule.models.calendar import (
    CheckinStatus,
    ClassCheckin,
    SpecialClassCheckin,
)


def get_student_checkin_history(person, limit=12):
    class_entries = [
        SimpleNamespace(
            is_special=False,
            date=checkin.session.date,
            start_time=checkin.session.schedule.start_time,
            start_time_label=checkin.session.schedule.start_time.strftime("%H:%M"),
            group_name=checkin.session.schedule.class_group.display_name,
            category_name=checkin.session.schedule.class_group.class_category.display_name,
            teacher_name=(
                checkin.session.schedule.class_group.main_teacher.full_name
                if checkin.session.schedule.class_group.main_teacher_id
                else ""
            ),
            checked_in_at=timezone.localtime(checkin.checked_in_at),
            approved_at=timezone.localtime(checkin.approved_at) if checkin.approved_at else None,
        )
        for checkin in ClassCheckin.objects.filter(
            person=person,
            status=CheckinStatus.APPROVED,
        )
        .select_related(
            "session__schedule__class_group",
            "session__schedule__class_group__class_category",
            "session__schedule__class_group__main_teacher",
        )
        .order_by("-session__date", "-session__schedule__start_time", "-checked_in_at")
    ]

    special_entries = [
        SimpleNamespace(
            is_special=True,
            date=checkin.special_class.date,
            start_time=checkin.special_class.start_time,
            start_time_label=checkin.special_class.start_time.strftime("%H:%M"),
            group_name=checkin.special_class.title,
            category_name="Aulão",
            teacher_name=(
                checkin.special_class.teacher.full_name
                if checkin.special_class.teacher_id
                else ""
            ),
            checked_in_at=timezone.localtime(checkin.checked_in_at),
            approved_at=timezone.localtime(checkin.approved_at) if checkin.approved_at else None,
        )
        for checkin in SpecialClassCheckin.objects.filter(
            person=person,
            status=CheckinStatus.APPROVED,
        )
        .select_related("special_class", "special_class__teacher")
        .order_by("-special_class__date", "-special_class__start_time", "-checked_in_at")
    ]

    history = class_entries + special_entries
    history.sort(
        key=lambda entry: (entry.date, entry.start_time, entry.checked_in_at),
        reverse=True,
    )
    return history[:limit]


@transaction.atomic
def perform_checkin(person, schedule_id):
    today = timezone.localdate()
    schedule = ClassSchedule.objects.select_related("class_group").get(pk=schedule_id)

    if schedule.class_group_id not in training_class_group_ids(person):
        raise PermissionError("Você não está matriculado nesta turma.")

    session, _ = ClassSession.objects.get_or_create(
        schedule=schedule,
        date=today,
        defaults=session_creation_defaults(),
    )

    if session.is_cancelled:
        raise ValueError("Esta aula foi cancelada.")

    holiday = Holiday.objects.filter(date=today, is_active=True).first()
    if holiday:
        raise ValueError(f"Hoje é feriado: {holiday.name}")

    membership = get_active_membership(person)
    pause = resolve_current_pause(membership)
    if pause is not None:
        raise ValueError(
            "Matrícula pausada até "
            f"{pause.requested_end_date.strftime('%d/%m/%Y')} — check-in indisponível."
        )

    checkin, created = ClassCheckin.objects.get_or_create(
        session=session,
        person=person,
        defaults={"status": CheckinStatus.PENDING},
    )
    if created:
        consume_trial_for_person(person)
    return checkin, created


@transaction.atomic
def cancel_student_checkin(person, schedule_id):
    today = timezone.localdate()
    schedule = ClassSchedule.objects.get(pk=schedule_id)
    session = ClassSession.objects.filter(schedule=schedule, date=today).first()
    if session is None:
        return None, False

    checkin = ClassCheckin.objects.filter(session=session, person=person).first()
    if checkin is None:
        return None, False
    if checkin.is_approved:
        raise ValueError("Check-in já aprovado não pode ser desfeito pelo aluno.")

    checkin.delete()
    return checkin, True


@transaction.atomic
def approve_class_checkin(*, instructor, checkin_id):
    checkin = (
        ClassCheckin.objects.select_related(
            "session",
            "session__schedule__class_group",
            "session__substitute_teacher",
        )
        .get(pk=checkin_id)
    )
    instructor_group_ids = get_instructor_class_group_ids(instructor)
    is_substitute = checkin.session.substitute_teacher_id == instructor.pk
    if checkin.session.schedule.class_group_id not in instructor_group_ids and not is_substitute:
        raise PermissionError("Você não é responsável por esta turma.")
    if checkin.session.is_cancelled:
        raise ValueError("Esta aula foi cancelada.")
    if checkin.is_approved:
        return checkin
    checkin.status = CheckinStatus.APPROVED
    checkin.approved_at = timezone.now()
    checkin.approved_by = instructor
    checkin.save(update_fields=["status", "approved_at", "approved_by", "updated_at"])
    return checkin


@transaction.atomic
def approve_special_checkin(*, instructor, checkin_id):
    checkin = (
        SpecialClassCheckin.objects.select_related("special_class", "special_class__substitute_teacher")
        .get(pk=checkin_id)
    )
    is_substitute = checkin.special_class.substitute_teacher_id == instructor.pk
    if checkin.special_class.teacher_id != instructor.pk and not is_substitute:
        raise PermissionError("Você não é responsável por este aulão.")
    if checkin.special_class.is_cancelled:
        raise ValueError("Este aulão foi cancelado.")
    if checkin.is_approved:
        return checkin
    checkin.status = CheckinStatus.APPROVED
    checkin.approved_at = timezone.now()
    checkin.approved_by = instructor
    checkin.save(update_fields=["status", "approved_at", "approved_by", "updated_at"])
    return checkin


@transaction.atomic
def perform_special_class_checkin(person, special_id):
    special = SpecialClass.objects.get(pk=special_id)
    today = timezone.localdate()
    if special.date != today:
        raise ValueError("Check-in só é permitido no dia do aulão.")
    if special.is_cancelled:
        raise ValueError("Este aulão foi cancelado.")
    checkin, created = SpecialClassCheckin.objects.get_or_create(
        special_class=special,
        person=person,
        defaults={"status": CheckinStatus.PENDING},
    )
    if created:
        consume_trial_for_person(person)
    return checkin, created


@transaction.atomic
def cancel_student_special_class_checkin(person, special_id):
    special = SpecialClass.objects.get(pk=special_id)
    today = timezone.localdate()
    if special.date != today:
        raise ValueError("Cancelamento de check-in só é permitido no dia do aulão.")

    checkin = SpecialClassCheckin.objects.filter(special_class=special, person=person).first()
    if checkin is None:
        return None, False
    if checkin.is_approved:
        raise ValueError("Check-in já aprovado não pode ser desfeito pelo aluno.")

    checkin.delete()
    return checkin, True
