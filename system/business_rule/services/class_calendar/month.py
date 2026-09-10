import calendar
from collections import OrderedDict
from datetime import date
from types import SimpleNamespace
from django.utils.formats import date_format
from django.utils import timezone
from system.business_rule.services.class_calendar.state import PYTHON_WEEKDAY_TO_CODE, get_month_name, special_cancel_state
from system.business_rule.models import ClassSchedule, ClassSession, Holiday, SpecialClass


def get_calendar_month_data(year, month):
    first_day = date(year, month, 1)
    _, num_days = calendar.monthrange(year, month)
    last_day = date(year, month, num_days)

    holidays = {
        h.date: h
        for h in Holiday.objects.filter(
            date__gte=first_day,
            date__lte=last_day,
            is_active=True,
        )
    }

    schedules = (
        ClassSchedule.objects.filter(is_active=True)
        .select_related("class_group", "class_group__class_category", "class_group__main_teacher")
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
        holiday = holidays.get(current_date)
        holiday_name = holiday.name if holiday else ""
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
            is_cancelled, cancellation_reason = special_cancel_state(sc, holiday)
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
                is_cancelled=is_cancelled,
                cancellation_reason=cancellation_reason,
            ))

        days.append(SimpleNamespace(
            date=current_date,
            day=day_num,
            weekday=date_format(current_date, "D"),
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
        month_name=get_month_name(month),
        days=days,
        prev_year=year if month > 1 else year - 1,
        prev_month=month - 1 if month > 1 else 12,
        next_year=year if month < 12 else year + 1,
        next_month=month + 1 if month < 12 else 1,
    )
