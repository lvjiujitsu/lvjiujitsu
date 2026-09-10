from types import SimpleNamespace
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from system.business_rule.services.class_calendar.authorization import can_instructor_access_session, can_instructor_access_special, get_instructor_class_group_ids
from system.business_rule.services.class_calendar.state import session_creation_defaults
from system.business_rule.models import ClassSchedule, ClassSession, SpecialClass
from system.business_rule.models.calendar import SessionStatus


def get_instructor_checkin_history(person, limit=12):
    class_group_ids = get_instructor_class_group_ids(person)

    class_entries = [
        SimpleNamespace(
            is_special=False,
            date=s.date,
            start_time=s.schedule.start_time,
            start_time_label=s.schedule.start_time.strftime("%H:%M"),
            group_name=s.schedule.class_group.display_name,
            category_name=s.schedule.class_group.class_category.display_name,
            checked_in_at=timezone.localtime(s.instructor_checked_in_at) if s.instructor_checked_in_at else None,
        )
        for s in ClassSession.objects.filter(
            Q(schedule__class_group_id__in=class_group_ids) | Q(substitute_teacher=person),
            instructor_present=True,
        )
        .select_related("schedule__class_group__class_category")
        .order_by("-date", "-schedule__start_time")
    ]

    special_entries = [
        SimpleNamespace(
            is_special=True,
            date=s.date,
            start_time=s.start_time,
            start_time_label=s.start_time.strftime("%H:%M"),
            group_name=s.title,
            category_name="Aulão",
            checked_in_at=timezone.localtime(s.instructor_checked_in_at) if s.instructor_checked_in_at else None,
        )
        for s in SpecialClass.objects.filter(
            Q(teacher=person) | Q(substitute_teacher=person),
            instructor_present=True,
        ).order_by("-date", "-start_time")
    ]

    history = class_entries + special_entries
    history.sort(key=lambda e: (e.date, e.start_time), reverse=True)
    return history[:limit]


@transaction.atomic
def register_instructor_self_checkin(instructor, schedule_id):
    today = timezone.localdate()
    schedule = ClassSchedule.objects.select_related("class_group").get(pk=schedule_id)

    session, _ = ClassSession.objects.get_or_create(
        schedule=schedule,
        date=today,
        defaults=session_creation_defaults(),
    )

    if not can_instructor_access_session(instructor, schedule, session):
        raise PermissionError("Você não é responsável por esta turma.")

    if session.substitute_teacher_id and session.substitute_teacher_id != instructor.pk:
        raise PermissionError("Outro professor foi indicado para esta aula.")

    if session.is_cancelled:
        raise ValueError("Esta aula foi cancelada.")

    if session.instructor_present:
        return session, False

    session.instructor_present = True
    session.instructor_checked_in_at = timezone.now()
    session.save(update_fields=["instructor_present", "instructor_checked_in_at", "updated_at"])
    return session, True


@transaction.atomic
def cancel_instructor_self_checkin(instructor, schedule_id):
    today = timezone.localdate()
    schedule = ClassSchedule.objects.select_related("class_group").get(pk=schedule_id)
    session = (
        ClassSession.objects.select_related("substitute_teacher")
        .filter(schedule=schedule, date=today)
        .first()
    )
    if session is None:
        session = ClassSession.objects.create(
            schedule=schedule,
            date=today,
            status=SessionStatus.SCHEDULED,
            instructor_present=False,
        )
        return session, True

    if not can_instructor_access_session(instructor, schedule, session):
        raise PermissionError("Você não é responsável por esta turma.")

    if session.substitute_teacher_id and session.substitute_teacher_id == instructor.pk:
        session.instructor_present = False
        session.instructor_checked_in_at = None
        session.substitute_teacher = None
        session.save(
            update_fields=[
                "instructor_present",
                "instructor_checked_in_at",
                "substitute_teacher",
                "updated_at",
            ]
        )
        return session, True

    if session.substitute_teacher_id and session.substitute_teacher_id != instructor.pk:
        raise PermissionError("A presença registrada pertence ao professor substituto.")

    if not session.instructor_present:
        return session, False

    session.instructor_present = False
    session.instructor_checked_in_at = None
    session.save(update_fields=["instructor_present", "instructor_checked_in_at", "updated_at"])
    return session, True


@transaction.atomic
def register_instructor_self_special_checkin(instructor, special_id):
    special = SpecialClass.objects.select_related("substitute_teacher").get(pk=special_id)

    if not can_instructor_access_special(instructor, special):
        raise PermissionError("Você não é responsável por este aulão.")

    today = timezone.localdate()
    if special.date != today:
        raise ValueError("Registro de presença só é permitido no dia do aulão.")

    if special.is_cancelled:
        raise ValueError("Este aulão foi cancelado.")

    if special.substitute_teacher_id and special.substitute_teacher_id != instructor.pk:
        raise PermissionError("Outro professor foi indicado para este aulão.")

    if special.instructor_present:
        return special, False

    special.instructor_present = True
    special.instructor_checked_in_at = timezone.now()
    special.save(update_fields=["instructor_present", "instructor_checked_in_at", "updated_at"])
    return special, True


@transaction.atomic
def cancel_instructor_self_special_checkin(instructor, special_id):
    special = SpecialClass.objects.select_related("substitute_teacher").get(pk=special_id)

    if not can_instructor_access_special(instructor, special):
        raise PermissionError("Você não é responsável por este aulão.")

    today = timezone.localdate()
    if special.date != today:
        raise ValueError("Cancelamento de presença só é permitido no dia do aulão.")

    if special.is_cancelled:
        raise ValueError("Este aulão foi cancelado.")

    if special.substitute_teacher_id and special.substitute_teacher_id == instructor.pk:
        special.instructor_present = False
        special.instructor_checked_in_at = None
        special.substitute_teacher = None
        special.save(
            update_fields=[
                "instructor_present",
                "instructor_checked_in_at",
                "substitute_teacher",
                "updated_at",
            ]
        )
        return special, True

    if special.substitute_teacher_id and special.substitute_teacher_id != instructor.pk:
        raise PermissionError("A presença registrada pertence ao professor substituto.")

    if not special.instructor_present:
        return special, False

    special.instructor_present = False
    special.instructor_checked_in_at = None
    special.save(update_fields=["instructor_present", "instructor_checked_in_at", "updated_at"])
    return special, True
