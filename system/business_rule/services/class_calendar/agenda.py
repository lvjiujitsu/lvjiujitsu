from types import SimpleNamespace
from django.utils import timezone
from system.business_rule.services.membership import get_active_membership
from system.business_rule.services.membership_resolution import resolve_current_pause
from system.business_rule.services.class_calendar.authorization import get_instructor_class_group_ids
from system.business_rule.services.class_calendar.state import (
    PYTHON_WEEKDAY_TO_CODE,
    SPECIAL_CATEGORY_NAME,
    build_instructor_special_entry,
    can_uncancel_class,
    instructor_checkin_view,
    instructor_presence_state,
    instructor_special_classes_for_person,
    session_cancellation,
    special_cancel_state,
    special_presence_state,
    student_session_entry,
    student_special_entry,
    training_class_group_ids,
)
from system.business_rule.models import ClassSchedule, ClassSession, Holiday, SpecialClass
from system.business_rule.models.calendar import ClassCheckin, SpecialClassCheckin


def get_today_classes_for_person(person):
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]

    enrollments = person.class_enrollments.filter(
        status="active",
    ).select_related("class_group")
    enrolled_group_ids = training_class_group_ids(person)

    specials = list(
        SpecialClass.objects.filter(date=today)
        .select_related("teacher")
        .order_by("start_time")
    )
    special_checkins_by_special_id = {
        checkin.special_class_id: checkin
        for checkin in SpecialClassCheckin.objects.filter(
            person=person,
            special_class__in=specials,
        )
    }
    holiday = Holiday.objects.filter(date=today, is_active=True).first()

    membership = get_active_membership(person)
    membership_pause = resolve_current_pause(membership)
    membership_paused_until = membership_pause.requested_end_date if membership_pause else None

    def _special_entries():
        return [
            student_special_entry(
                sc,
                special_checkins_by_special_id.get(sc.pk),
                holiday,
                pause=membership_pause,
                paused_until=membership_paused_until,
            )
            for sc in specials
        ]

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

    sessions_map = {}
    existing_sessions = ClassSession.objects.filter(
        schedule__in=schedules,
        date=today,
    )
    for session in existing_sessions:
        sessions_map[session.schedule_id] = session

    checkins_by_session_id = {
        checkin.session_id: checkin
        for checkin in ClassCheckin.objects.filter(
            person=person,
            session__date=today,
        )
    }

    result = []
    for schedule in schedules:
        session = sessions_map.get(schedule.pk)
        result.append(
            student_session_entry(
                schedule,
                session,
                checkins_by_session_id.get(session.pk) if session else None,
                holiday,
                pause=membership_pause,
                paused_until=membership_paused_until,
            )
        )
    result.extend(_special_entries())
    return result


def get_today_classes_for_instructor(person):
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]
    class_group_ids = get_instructor_class_group_ids(person)

    schedules = list(
        ClassSchedule.objects.filter(
            class_group_id__in=class_group_ids,
            weekday=weekday_code,
            is_active=True,
        )
        .select_related("class_group", "class_group__class_category")
        .order_by("start_time")
    )
    substitute_sessions = list(
        ClassSession.objects.filter(
            date=today,
            substitute_teacher=person,
            schedule__weekday=weekday_code,
            schedule__is_active=True,
        )
        .exclude(schedule__class_group_id__in=class_group_ids)
        .select_related("schedule", "schedule__class_group", "schedule__class_group__class_category", "substitute_teacher")
        .order_by("schedule__start_time")
    )
    seen_schedule_ids = {schedule.pk for schedule in schedules}
    for session in substitute_sessions:
        if session.schedule_id in seen_schedule_ids:
            continue
        schedules.append(session.schedule)
        seen_schedule_ids.add(session.schedule_id)
    schedules.sort(key=lambda schedule: schedule.start_time)

    sessions = list(
        ClassSession.objects.filter(schedule__in=schedules, date=today)
        .select_related("schedule", "substitute_teacher")
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
        substitute_teacher = session.substitute_teacher if session else None
        is_original_instructor = schedule.class_group_id in class_group_ids
        is_substitute_assignment = bool(
            substitute_teacher and substitute_teacher.pk == person.pk and not is_original_instructor
        )
        presence = instructor_presence_state(
            session,
            viewer=person,
            is_original_instructor=is_original_instructor,
            substitute_teacher=substitute_teacher,
        )
        is_cancelled = (session and session.is_cancelled) or bool(holiday)
        cancellation_reason = ""
        if holiday:
            cancellation_reason = holiday.name
        elif session and session.is_cancelled:
            cancellation_reason = session.cancellation_reason
        entries.append(
            SimpleNamespace(
                entry_role="instructor",
                is_special=False,
                schedule=schedule,
                schedule_id=schedule.pk,
                session=session,
                session_date=today,
                start_time=schedule.start_time.strftime("%H:%M"),
                date=today,
                group_name=schedule.class_group.display_name,
                category_name=schedule.class_group.class_category.display_name,
                duration_minutes=schedule.duration_minutes,
                is_cancelled=is_cancelled,
                is_holiday_cancelled=bool(holiday),
                cancellation_reason=cancellation_reason,
                checkins=[instructor_checkin_view(c, is_special=False) for c in session_checkins],
                checked_count=len(session_checkins),
                approved_count=sum(1 for c in session_checkins if c.is_approved),
                pending_count=sum(1 for c in session_checkins if not c.is_approved),
                instructor_present=presence["instructor_present"],
                instructor_checked_in_at=presence["instructor_checked_in_at"],
                substitute_teacher_id=presence["substitute_teacher_id"],
                substitute_teacher_name=presence["substitute_teacher_name"],
                substitute_confirmed=presence.get("substitute_confirmed", False),
                substitute_pending=presence.get("substitute_pending", False),
                is_substitute_assignment=is_substitute_assignment,
                can_self_checkin=presence["can_confirm_presence"],
                can_confirm_presence=presence["can_confirm_presence"],
                can_cancel_presence=presence["can_cancel_presence"],
                can_assign_substitute=presence["can_assign_substitute"],
                can_cancel_class=presence.get("can_cancel_class", False),
                can_uncancel_class=can_uncancel_class(
                    session=session,
                    is_cancelled=is_cancelled,
                    is_holiday_cancelled=bool(holiday),
                    is_original_instructor=is_original_instructor,
                ),
            )
        )

    special_classes = instructor_special_classes_for_person(person, today)
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
        presence = special_presence_state(special, viewer=person)
        entries.append(
            build_instructor_special_entry(
                special=special,
                person=person,
                today=today,
                holiday=holiday,
                checkins=special_class_checkins,
                presence=presence,
            )
        )

    return entries


def get_today_classes_for_administrative(person):
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]
    instructor_group_ids = set(get_instructor_class_group_ids(person))
    holiday = Holiday.objects.filter(date=today, is_active=True).first()
    entries = []

    if instructor_group_ids:
        schedules = (
            ClassSchedule.objects.filter(
                class_group_id__in=instructor_group_ids,
                weekday=weekday_code,
                is_active=True,
            )
            .select_related("class_group", "class_group__class_category")
            .order_by("start_time")
        )
        sessions = list(
            ClassSession.objects.filter(schedule__in=schedules, date=today).select_related(
                "schedule", "substitute_teacher"
            )
        )
        sessions_by_schedule_id = {s.schedule_id: s for s in sessions}
        raw_checkins = list(
            ClassCheckin.objects.filter(session__in=sessions)
            .select_related("person", "session")
            .order_by("session__schedule__start_time", "person__full_name")
        )
        checkins_by_session_id = {}
        for c in raw_checkins:
            checkins_by_session_id.setdefault(c.session_id, []).append(c)

        for schedule in schedules:
            session = sessions_by_schedule_id.get(schedule.pk)
            session_checkins = checkins_by_session_id.get(session.pk, []) if session else []
            substitute_teacher = session.substitute_teacher if session else None
            presence = instructor_presence_state(
                session,
                viewer=person,
                is_original_instructor=True,
                substitute_teacher=substitute_teacher,
            )
            is_cancelled = (session and session.is_cancelled) or bool(holiday)
            cancellation_reason = ""
            if holiday:
                cancellation_reason = holiday.name
            elif session and session.is_cancelled:
                cancellation_reason = session.cancellation_reason
            entries.append(SimpleNamespace(
                entry_role="instructor",
                is_special=False,
                special_id=None,
                schedule=schedule,
                schedule_id=schedule.pk,
                session=session,
                session_date=today,
                start_time=schedule.start_time.strftime("%H:%M"),
                date=today,
                group_name=schedule.class_group.display_name,
                category_name=schedule.class_group.class_category.display_name,
                duration_minutes=schedule.duration_minutes,
                is_cancelled=is_cancelled,
                is_holiday_cancelled=bool(holiday),
                cancellation_reason=cancellation_reason,
                checkins=[instructor_checkin_view(c, is_special=False) for c in session_checkins],
                checked_count=len(session_checkins),
                approved_count=sum(1 for c in session_checkins if c.is_approved),
                pending_count=sum(1 for c in session_checkins if not c.is_approved),
                instructor_present=presence["instructor_present"],
                instructor_checked_in_at=presence["instructor_checked_in_at"],
                substitute_teacher_id=presence["substitute_teacher_id"],
                substitute_teacher_name=presence["substitute_teacher_name"],
                substitute_confirmed=presence.get("substitute_confirmed", False),
                substitute_pending=presence.get("substitute_pending", False),
                is_substitute_assignment=False,
                can_self_checkin=presence["can_confirm_presence"],
                can_confirm_presence=presence["can_confirm_presence"],
                can_cancel_presence=presence["can_cancel_presence"],
                can_assign_substitute=presence["can_assign_substitute"],
                can_cancel_class=presence.get("can_cancel_class", False),
                can_uncancel_class=can_uncancel_class(
                    session=session,
                    is_cancelled=is_cancelled,
                    is_holiday_cancelled=bool(holiday),
                    is_original_instructor=True,
                ),
            ))

    training_group_id = (
        person.class_group_id
        if person.class_group_id and person.class_group_id not in instructor_group_ids
        else None
    )
    student_group_ids = [training_group_id] if training_group_id else []
    if student_group_ids:
        student_schedules = (
            ClassSchedule.objects.filter(
                class_group_id__in=student_group_ids,
                weekday=weekday_code,
                is_active=True,
            )
            .select_related("class_group", "class_group__class_category", "class_group__main_teacher")
            .order_by("start_time")
        )
        student_sessions_map = {}
        for s in ClassSession.objects.filter(schedule__in=student_schedules, date=today):
            student_sessions_map[s.schedule_id] = s
        student_checkins_by_session = {
            c.session_id: c
            for c in ClassCheckin.objects.filter(person=person, session__date=today)
        }
        for schedule in student_schedules:
            session = student_sessions_map.get(schedule.pk)
            entries.append(
                student_session_entry(
                    schedule,
                    session,
                    student_checkins_by_session.get(session.pk) if session else None,
                    holiday,
                )
            )

    all_specials = list(
        SpecialClass.objects.filter(date=today)
        .select_related("teacher", "substitute_teacher")
        .order_by("start_time")
    )
    instructor_special_ids = [
        s.pk for s in all_specials
        if s.teacher_id == person.pk or s.substitute_teacher_id == person.pk
    ]
    instructor_special_checkins_by_id = {}
    if instructor_special_ids:
        for c in (
            SpecialClassCheckin.objects.filter(special_class_id__in=instructor_special_ids)
            .select_related("person", "special_class")
            .order_by("special_class__start_time", "person__full_name")
        ):
            instructor_special_checkins_by_id.setdefault(c.special_class_id, []).append(c)

    student_special_ids = [
        s.pk for s in all_specials
        if s.teacher_id != person.pk and s.substitute_teacher_id != person.pk
    ]
    student_special_checkins_by_id = {
        c.special_class_id: c
        for c in SpecialClassCheckin.objects.filter(person=person, special_class_id__in=student_special_ids)
    }

    for special in all_specials:
        if special.teacher_id == person.pk or special.substitute_teacher_id == person.pk:
            special_class_checkins = instructor_special_checkins_by_id.get(special.pk, [])
            presence = special_presence_state(special, viewer=person)
            entries.append(
                build_instructor_special_entry(
                    special=special,
                    person=person,
                    today=today,
                    holiday=holiday,
                    checkins=special_class_checkins,
                    presence=presence,
                )
            )
        else:
            entries.append(
                student_special_entry(
                    special,
                    student_special_checkins_by_id.get(special.pk),
                    holiday,
                )
            )

    entries.sort(key=lambda e: e.start_time)
    return entries


def get_today_classes_staff_overview():
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]
    holiday = Holiday.objects.filter(date=today, is_active=True).first()

    schedules = (
        ClassSchedule.objects.filter(weekday=weekday_code, is_active=True)
        .select_related(
            "class_group",
            "class_group__class_category",
            "class_group__main_teacher",
        )
        .order_by("start_time")
    )
    sessions = list(
        ClassSession.objects.filter(schedule__in=schedules, date=today).select_related("schedule")
    )
    sessions_by_schedule_id = {session.schedule_id: session for session in sessions}
    checkins_by_session_id = {}
    for checkin in ClassCheckin.objects.filter(session__in=sessions).select_related("session"):
        checkins_by_session_id.setdefault(checkin.session_id, []).append(checkin)

    entries = []
    for schedule in schedules:
        session = sessions_by_schedule_id.get(schedule.pk)
        session_checkins = checkins_by_session_id.get(session.pk, []) if session else []
        is_cancelled, cancellation_reason = session_cancellation(session, holiday)
        teacher = schedule.class_group.main_teacher
        entries.append(
            SimpleNamespace(
                entry_role="overview",
                is_special=False,
                special_id=None,
                schedule=schedule,
                schedule_id=schedule.pk,
                session=session,
                start_time=schedule.start_time.strftime("%H:%M"),
                group_name=schedule.class_group.display_name,
                category_name=schedule.class_group.class_category.display_name,
                teacher_name=teacher.full_name if teacher else "",
                duration_minutes=schedule.duration_minutes,
                is_cancelled=is_cancelled,
                cancellation_reason=cancellation_reason,
                approved_count=sum(1 for c in session_checkins if c.is_approved),
                pending_count=sum(1 for c in session_checkins if not c.is_approved),
            )
        )

    specials_today = list(
        SpecialClass.objects.filter(date=today).select_related("teacher").order_by("start_time")
    )
    special_checkins_by_special_id = {}
    for checkin in SpecialClassCheckin.objects.filter(special_class__in=specials_today).select_related("person"):
        special_checkins_by_special_id.setdefault(checkin.special_class_id, []).append(checkin)

    for special in specials_today:
        special_checkins = special_checkins_by_special_id.get(special.pk, [])
        is_cancelled, cancellation_reason = special_cancel_state(special, holiday)
        entries.append(
            SimpleNamespace(
                entry_role="overview",
                is_special=True,
                special_id=special.pk,
                schedule=None,
                schedule_id=None,
                session=None,
                start_time=special.start_time.strftime("%H:%M"),
                group_name=special.title,
                category_name=SPECIAL_CATEGORY_NAME,
                teacher_name=special.teacher.full_name if special.teacher else "",
                duration_minutes=special.duration_minutes,
                is_cancelled=is_cancelled,
                cancellation_reason=cancellation_reason,
                approved_count=sum(1 for c in special_checkins if c.is_approved),
                pending_count=sum(1 for c in special_checkins if not c.is_approved),
            )
        )

    entries.sort(key=lambda entry: entry.start_time)
    return entries
