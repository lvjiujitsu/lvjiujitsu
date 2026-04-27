import calendar
from collections import OrderedDict
from datetime import date, timedelta
from types import SimpleNamespace

from django.conf import settings
from django.db import transaction
from django.utils.formats import date_format
from django.utils import timezone

from system.models import (
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    WeekdayCode,
)
from system.models.calendar import (
    ClassCheckin,
    ClassSession,
    Holiday,
    SessionStatus,
    SpecialClass,
    SpecialClassCheckin,
)
from system.services.trial_access import consume_trial_for_person


PYTHON_WEEKDAY_TO_CODE = {
    0: WeekdayCode.MONDAY,
    1: WeekdayCode.TUESDAY,
    2: WeekdayCode.WEDNESDAY,
    3: WeekdayCode.THURSDAY,
    4: WeekdayCode.FRIDAY,
    5: WeekdayCode.SATURDAY,
    6: WeekdayCode.SUNDAY,
}


def get_today_classes_for_person(person):
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]

    enrollments = person.class_enrollments.filter(
        status="active",
    ).select_related("class_group")
    enrolled_group_ids = [e.class_group_id for e in enrollments]

    specials = list(
        SpecialClass.objects.filter(date=today)
        .select_related("teacher")
        .order_by("start_time")
    )
    special_checkin_ids = set(
        SpecialClassCheckin.objects.filter(
            person=person,
            special_class__in=specials,
        ).values_list("special_class_id", flat=True)
    )

    def _special_entries():
        entries = []
        for sc in specials:
            entries.append(SimpleNamespace(
                is_special=True,
                special_class=sc,
                special_id=sc.pk,
                schedule=None,
                session=None,
                class_group=None,
                start_time=sc.start_time.strftime("%H:%M"),
                duration_minutes=sc.duration_minutes,
                training_style="",
                teacher_name=sc.teacher.full_name if sc.teacher else "",
                category_name="",
                group_name=sc.title,
                is_cancelled=False,
                cancellation_reason="",
                has_checked_in=sc.pk in special_checkin_ids,
            ))
        return entries

    if not enrolled_group_ids:
        return _special_entries()

    schedules = (
        ClassSchedule.objects.filter(
            class_group_id__in=enrolled_group_ids,
            weekday=weekday_code,
            is_active=True,
        )
        .select_related("class_group", "class_group__class_category", "class_group__main_teacher")
        .order_by("start_time")
    )

    holiday = Holiday.objects.filter(date=today, is_active=True).first()

    sessions_map = {}
    existing_sessions = ClassSession.objects.filter(
        schedule__in=schedules,
        date=today,
    )
    for session in existing_sessions:
        sessions_map[session.schedule_id] = session

    checkin_session_ids = set(
        ClassCheckin.objects.filter(
            person=person,
            session__date=today,
        ).values_list("session_id", flat=True)
    )

    result = []
    for schedule in schedules:
        session = sessions_map.get(schedule.pk)
        is_cancelled = (session and session.is_cancelled) or bool(holiday)
        cancellation_reason = ""
        if holiday:
            cancellation_reason = holiday.name
        elif session and session.is_cancelled:
            cancellation_reason = session.cancellation_reason

        has_checked_in = session.pk in checkin_session_ids if session else False

        result.append(SimpleNamespace(
            is_special=False,
            special_class=None,
            special_id=None,
            schedule=schedule,
            session=session,
            class_group=schedule.class_group,
            start_time=schedule.start_time.strftime("%H:%M"),
            duration_minutes=schedule.duration_minutes,
            training_style=schedule.get_training_style_display(),
            teacher_name=schedule.class_group.main_teacher.full_name if schedule.class_group.main_teacher else "",
            category_name=schedule.class_group.class_category.display_name,
            group_name=schedule.class_group.display_name,
            is_cancelled=is_cancelled,
            cancellation_reason=cancellation_reason,
            has_checked_in=has_checked_in,
        ))
    result.extend(_special_entries())
    return result


def get_today_classes_for_instructor(person):
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]
    class_group_ids = _get_instructor_class_group_ids(person)

    schedules = (
        ClassSchedule.objects.filter(
            class_group_id__in=class_group_ids,
            weekday=weekday_code,
            is_active=True,
        )
        .select_related("class_group", "class_group__class_category")
        .order_by("start_time")
    )
    sessions = list(
        ClassSession.objects.filter(schedule__in=schedules, date=today).select_related("schedule")
    )
    sessions_by_schedule_id = {session.schedule_id: session for session in sessions}

    checkins = list(
        ClassCheckin.objects.filter(session__in=sessions)
        .select_related("person", "session")
        .order_by("session__schedule__start_time", "person__full_name")
    )
    checkins_by_session_id = {}
    for checkin in checkins:
        checkins_by_session_id.setdefault(checkin.session_id, []).append(checkin)

    holiday = Holiday.objects.filter(date=today, is_active=True).first()
    entries = []
    for schedule in schedules:
        session = sessions_by_schedule_id.get(schedule.pk)
        session_checkins = checkins_by_session_id.get(session.pk, []) if session else []
        is_cancelled = (session and session.is_cancelled) or bool(holiday)
        cancellation_reason = ""
        if holiday:
            cancellation_reason = holiday.name
        elif session and session.is_cancelled:
            cancellation_reason = session.cancellation_reason
        entries.append(
            SimpleNamespace(
                is_special=False,
                start_time=schedule.start_time.strftime("%H:%M"),
                date=today,
                group_name=schedule.class_group.display_name,
                category_name=schedule.class_group.class_category.display_name,
                duration_minutes=schedule.duration_minutes,
                is_cancelled=is_cancelled,
                cancellation_reason=cancellation_reason,
                checked_students=[checkin.person.full_name for checkin in session_checkins],
                checked_count=len(session_checkins),
            )
        )

    special_classes = list(
        SpecialClass.objects.filter(date=today, teacher=person).order_by("start_time")
    )
    special_checkins = list(
        SpecialClassCheckin.objects.filter(special_class__in=special_classes)
        .select_related("person", "special_class")
        .order_by("special_class__start_time", "person__full_name")
    )
    checkins_by_special_id = {}
    for checkin in special_checkins:
        checkins_by_special_id.setdefault(checkin.special_class_id, []).append(checkin)

    for special in special_classes:
        special_class_checkins = checkins_by_special_id.get(special.pk, [])
        entries.append(
            SimpleNamespace(
                is_special=True,
                start_time=special.start_time.strftime("%H:%M"),
                date=today,
                group_name=special.title,
                category_name="Aulão",
                duration_minutes=special.duration_minutes,
                is_cancelled=False,
                cancellation_reason="",
                checked_students=[checkin.person.full_name for checkin in special_class_checkins],
                checked_count=len(special_class_checkins),
            )
        )

    return entries


def get_instructor_checkin_history(person, limit=12):
    class_group_ids = _get_instructor_class_group_ids(person)

    class_checkins = (
        ClassCheckin.objects.filter(session__schedule__class_group_id__in=class_group_ids)
        .select_related("person", "session__schedule__class_group", "session__schedule__class_group__class_category")
        .order_by("-session__date", "-session__schedule__start_time", "person__full_name")
    )
    class_entries = []
    class_history_by_session_id = {}
    for checkin in class_checkins:
        session_id = checkin.session_id
        if session_id not in class_history_by_session_id:
            class_history_by_session_id[session_id] = SimpleNamespace(
                is_special=False,
                date=checkin.session.date,
                start_time=checkin.session.schedule.start_time,
                start_time_label=checkin.session.schedule.start_time.strftime("%H:%M"),
                group_name=checkin.session.schedule.class_group.display_name,
                category_name=checkin.session.schedule.class_group.class_category.display_name,
                attendees=[],
            )
            class_entries.append(class_history_by_session_id[session_id])
        class_history_by_session_id[session_id].attendees.append(checkin.person.full_name)

    special_checkins = (
        SpecialClassCheckin.objects.filter(special_class__teacher=person)
        .select_related("person", "special_class")
        .order_by("-special_class__date", "-special_class__start_time", "person__full_name")
    )
    special_entries = []
    special_history_by_class_id = {}
    for checkin in special_checkins:
        special_id = checkin.special_class_id
        if special_id not in special_history_by_class_id:
            special_history_by_class_id[special_id] = SimpleNamespace(
                is_special=True,
                date=checkin.special_class.date,
                start_time=checkin.special_class.start_time,
                start_time_label=checkin.special_class.start_time.strftime("%H:%M"),
                group_name=checkin.special_class.title,
                category_name="Aulão",
                attendees=[],
            )
            special_entries.append(special_history_by_class_id[special_id])
        special_history_by_class_id[special_id].attendees.append(checkin.person.full_name)

    history = class_entries + special_entries
    history.sort(
        key=lambda entry: (entry.date, entry.start_time),
        reverse=True,
    )
    return history[:limit]


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
        )
        for checkin in ClassCheckin.objects.filter(person=person)
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
        )
        for checkin in SpecialClassCheckin.objects.filter(person=person)
        .select_related("special_class", "special_class__teacher")
        .order_by("-special_class__date", "-special_class__start_time", "-checked_in_at")
    ]

    history = class_entries + special_entries
    history.sort(
        key=lambda entry: (entry.date, entry.start_time, entry.checked_in_at),
        reverse=True,
    )
    return history[:limit]


def _get_instructor_class_group_ids(person):
    main_teacher_group_ids = set(
        ClassGroup.objects.filter(main_teacher=person, is_active=True).values_list("pk", flat=True)
    )
    assignment_group_ids = set(
        ClassInstructorAssignment.objects.filter(
            person=person,
            class_group__is_active=True,
        ).values_list("class_group_id", flat=True)
    )
    return list(main_teacher_group_ids | assignment_group_ids)


@transaction.atomic
def perform_checkin(person, schedule_id):
    today = timezone.localdate()
    schedule = ClassSchedule.objects.select_related("class_group").get(pk=schedule_id)

    session, _ = ClassSession.objects.get_or_create(
        schedule=schedule,
        date=today,
        defaults={"status": SessionStatus.SCHEDULED},
    )

    if session.is_cancelled:
        raise ValueError("Esta aula foi cancelada.")

    holiday = Holiday.objects.filter(date=today, is_active=True).first()
    if holiday:
        raise ValueError(f"Hoje é feriado: {holiday.name}")

    checkin, created = ClassCheckin.objects.get_or_create(
        session=session,
        person=person,
    )
    if created:
        consume_trial_for_person(person)
    return checkin, created


def get_calendar_month_data(year, month):
    first_day = date(year, month, 1)
    _, num_days = calendar.monthrange(year, month)
    last_day = date(year, month, num_days)

    holidays = {
        h.date: h.name
        for h in Holiday.objects.filter(
            date__gte=first_day,
            date__lte=last_day,
            is_active=True,
        )
    }

    schedules = (
        ClassSchedule.objects.filter(is_active=True)
        .select_related("class_group", "class_group__class_category")
        .order_by("start_time")
    )

    schedules_by_weekday = OrderedDict()
    for schedule in schedules:
        schedules_by_weekday.setdefault(schedule.weekday, []).append(schedule)

    sessions_map = {}
    sessions = ClassSession.objects.filter(
        date__gte=first_day,
        date__lte=last_day,
    ).select_related("schedule")
    for session in sessions:
        sessions_map.setdefault(session.date, {})[session.schedule_id] = session

    specials_by_date = {}
    for sc in (
        SpecialClass.objects.filter(date__gte=first_day, date__lte=last_day)
        .select_related("teacher")
        .order_by("start_time")
    ):
        specials_by_date.setdefault(sc.date, []).append(sc)

    days = []
    for day_num in range(1, num_days + 1):
        current_date = date(year, month, day_num)
        weekday_code = PYTHON_WEEKDAY_TO_CODE[current_date.weekday()]
        holiday_name = holidays.get(current_date, "")
        day_schedules = schedules_by_weekday.get(weekday_code, [])
        day_sessions = sessions_map.get(current_date, {})

        class_entries = []
        for schedule in day_schedules:
            session = day_sessions.get(schedule.pk)
            is_cancelled = (session and session.is_cancelled) or bool(holiday_name)
            class_entries.append(SimpleNamespace(
                is_special=False,
                special_id=None,
                schedule_id=schedule.pk,
                session_id=session.pk if session else None,
                start_time=schedule.start_time.strftime("%H:%M"),
                group_name=schedule.class_group.display_name,
                category_name=schedule.class_group.class_category.display_name,
                teacher_name=(
                    schedule.class_group.main_teacher.full_name
                    if schedule.class_group.main_teacher
                    else ""
                ),
                is_cancelled=is_cancelled,
                cancellation_reason=session.cancellation_reason if session and session.is_cancelled else holiday_name,
            ))

        special_entries = []
        for sc in specials_by_date.get(current_date, []):
            special_entries.append(SimpleNamespace(
                is_special=True,
                special_id=sc.pk,
                schedule_id=None,
                session_id=None,
                start_time=sc.start_time.strftime("%H:%M"),
                group_name=sc.title,
                category_name="Aulão",
                teacher_name=sc.teacher.full_name if sc.teacher else "",
                notes=sc.notes,
                is_cancelled=False,
                cancellation_reason="",
            ))

        days.append(SimpleNamespace(
            date=current_date,
            day=day_num,
            weekday=current_date.strftime("%a"),
            is_today=current_date == timezone.localdate(),
            is_holiday=bool(holiday_name),
            holiday_name=holiday_name,
            classes=class_entries,
            specials=special_entries,
            has_classes=len(class_entries) > 0 or len(special_entries) > 0,
        ))

    return SimpleNamespace(
        year=year,
        month=month,
        month_name=_get_month_name(month),
        days=days,
        prev_year=year if month > 1 else year - 1,
        prev_month=month - 1 if month > 1 else 12,
        next_year=year if month < 12 else year + 1,
        next_month=month + 1 if month < 12 else 1,
    )


@transaction.atomic
def toggle_session_cancel(schedule_id, session_date, reason=""):
    schedule = ClassSchedule.objects.get(pk=schedule_id)
    session, created = ClassSession.objects.get_or_create(
        schedule=schedule,
        date=session_date,
        defaults={"status": SessionStatus.SCHEDULED},
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
    date,
    start_time,
    duration_minutes=None,
    teacher=None,
    notes="",
):
    if not title:
        title = settings.SPECIAL_CLASS_DEFAULT_TITLE
    special = SpecialClass.objects.create(
        title=title,
        date=date,
        start_time=start_time,
        duration_minutes=duration_minutes or settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES,
        teacher=teacher,
        notes=notes or "",
    )
    return special


@transaction.atomic
def delete_special_class(special_id):
    SpecialClass.objects.filter(pk=special_id).delete()


@transaction.atomic
def perform_special_class_checkin(person, special_id):
    special = SpecialClass.objects.get(pk=special_id)
    today = timezone.localdate()
    if special.date != today:
        raise ValueError("Check-in só é permitido no dia do aulão.")
    checkin, created = SpecialClassCheckin.objects.get_or_create(
        special_class=special,
        person=person,
    )
    if created:
        consume_trial_for_person(person)
    return checkin, created


def _get_month_name(month):
    return date_format(date(2000, month, 1), "F")
