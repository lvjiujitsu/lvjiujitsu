import calendar
from collections import OrderedDict
from datetime import date, timedelta
from types import SimpleNamespace

from django.db import transaction
from django.utils import timezone

from system.models import ClassSchedule, WeekdayCode
from system.models.calendar import ClassCheckin, ClassSession, Holiday, SessionStatus


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

    if not enrolled_group_ids:
        return []

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
    return result


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
                schedule_id=schedule.pk,
                session_id=session.pk if session else None,
                start_time=schedule.start_time.strftime("%H:%M"),
                group_name=schedule.class_group.display_name,
                category_name=schedule.class_group.class_category.display_name,
                is_cancelled=is_cancelled,
                cancellation_reason=session.cancellation_reason if session and session.is_cancelled else holiday_name,
            ))

        days.append(SimpleNamespace(
            date=current_date,
            day=day_num,
            weekday=current_date.strftime("%a"),
            is_today=current_date == timezone.localdate(),
            is_holiday=bool(holiday_name),
            holiday_name=holiday_name,
            classes=class_entries,
            has_classes=len(class_entries) > 0,
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


def _get_month_name(month):
    names = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    return names.get(month, "")
