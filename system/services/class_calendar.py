import calendar
from collections import OrderedDict
from datetime import date
from types import SimpleNamespace

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.formats import date_format
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    WeekdayCode,
)
from system.models.calendar import (
    CheckinStatus,
    ClassCheckin,
    ClassSession,
    Holiday,
    SessionStatus,
    SpecialClass,
    SpecialClassCheckin,
)
from system.services.membership import get_active_membership
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


def _student_instructor_present(session):
    if session is None:
        return True
    return session.instructor_present


def _training_class_group_ids(person):
    enrolled_group_ids = list(
        person.class_enrollments.filter(status="active").values_list(
            "class_group_id", flat=True
        )
    )
    if person.class_group_id and person.class_group_id not in enrolled_group_ids:
        enrolled_group_ids.append(person.class_group_id)
    return enrolled_group_ids


def _instructor_presence_state(session, *, viewer, is_original_instructor, substitute_teacher):
    substitute = substitute_teacher
    delegated_to_other = bool(
        substitute and is_original_instructor and substitute.pk != viewer.pk
    )
    if delegated_to_other:
        substitute_confirmed = bool(session and session.instructor_present)
        checked_at = None
        if substitute_confirmed and session.instructor_checked_in_at:
            checked_at = timezone.localtime(session.instructor_checked_in_at)
        return {
            "instructor_present": substitute_confirmed,
            "instructor_checked_in_at": checked_at,
            "substitute_teacher_id": substitute.pk,
            "substitute_teacher_name": substitute.full_name,
            "substitute_confirmed": substitute_confirmed,
            "substitute_pending": not substitute_confirmed,
            "can_confirm_presence": False,
            "can_cancel_presence": False,
            "can_assign_substitute": False,
            "can_cancel_class": False,
        }

    effective_present = session.instructor_present if session else True
    checked_at = None
    if effective_present and session and session.instructor_checked_in_at:
        checked_at = timezone.localtime(session.instructor_checked_in_at)

    if effective_present:
        can_cancel = (is_original_instructor and not substitute) or (
            substitute and substitute.pk == viewer.pk
        )
        return {
            "instructor_present": True,
            "instructor_checked_in_at": checked_at,
            "substitute_teacher_id": substitute.pk if substitute else None,
            "substitute_teacher_name": substitute.full_name if substitute else "",
            "substitute_confirmed": bool(substitute),
            "substitute_pending": False,
            "can_confirm_presence": False,
            "can_cancel_presence": can_cancel,
            "can_assign_substitute": False,
            "can_cancel_class": False,
        }

    can_confirm = not substitute or substitute.pk == viewer.pk
    return {
        "instructor_present": False,
        "instructor_checked_in_at": None,
        "substitute_teacher_id": substitute.pk if substitute else None,
        "substitute_teacher_name": substitute.full_name if substitute else "",
        "substitute_confirmed": False,
        "substitute_pending": bool(substitute),
        "can_confirm_presence": can_confirm,
        "can_cancel_presence": False,
        "can_assign_substitute": is_original_instructor and substitute is None,
        "can_cancel_class": is_original_instructor and substitute is None,
    }


def _can_uncancel_class(*, session, is_cancelled, is_holiday_cancelled, is_original_instructor):
    return bool(
        is_cancelled
        and not is_holiday_cancelled
        and is_original_instructor
        and session
        and session.is_cancelled
    )


def _can_uncancel_special(*, special, is_cancelled, is_holiday_cancelled):
    return bool(
        is_cancelled
        and not is_holiday_cancelled
        and special
        and special.is_cancelled
    )


def _special_cancel_state(special, holiday):
    is_cancelled = (special and special.is_cancelled) or bool(holiday)
    cancellation_reason = ""
    if holiday:
        cancellation_reason = holiday.name
    elif special and special.is_cancelled:
        cancellation_reason = special.cancellation_reason
    return is_cancelled, cancellation_reason


def _special_presence_state(special, *, viewer):
    if special.is_cancelled:
        return {
            "instructor_present": False,
            "instructor_checked_in_at": None,
            "substitute_teacher_id": None,
            "substitute_teacher_name": "",
            "substitute_confirmed": False,
            "substitute_pending": False,
            "can_confirm_presence": False,
            "can_cancel_presence": False,
            "can_assign_substitute": False,
            "can_cancel_class": False,
        }
    is_original_instructor = special.teacher_id == viewer.pk
    return _instructor_presence_state(
        special,
        viewer=viewer,
        is_original_instructor=is_original_instructor,
        substitute_teacher=special.substitute_teacher,
    )


def _instructor_special_classes_for_person(person, today):
    return list(
        SpecialClass.objects.filter(date=today)
        .filter(Q(teacher=person) | Q(substitute_teacher=person))
        .select_related("teacher", "substitute_teacher")
        .order_by("start_time")
    )


def _build_instructor_special_entry(*, special, person, today, holiday, checkins, presence):
    is_cancelled, cancellation_reason = _special_cancel_state(special, holiday)
    is_original_instructor = special.teacher_id == person.pk
    is_substitute_assignment = bool(
        special.substitute_teacher_id == person.pk and not is_original_instructor
    )
    return SimpleNamespace(
        entry_role="instructor",
        is_special=True,
        special_class=special,
        special_id=special.pk,
        start_time=special.start_time.strftime("%H:%M"),
        date=today,
        group_name=special.title,
        category_name="Aulão",
        duration_minutes=special.duration_minutes,
        is_cancelled=is_cancelled,
        is_holiday_cancelled=bool(holiday),
        cancellation_reason=cancellation_reason,
        checkins=[_instructor_checkin_view(c, is_special=True) for c in checkins],
        checked_count=len(checkins),
        approved_count=sum(1 for c in checkins if c.is_approved),
        pending_count=sum(1 for c in checkins if not c.is_approved),
        instructor_present=presence["instructor_present"],
        instructor_checked_in_at=presence["instructor_checked_in_at"],
        substitute_teacher_id=presence.get("substitute_teacher_id"),
        substitute_teacher_name=presence.get("substitute_teacher_name", ""),
        substitute_confirmed=presence.get("substitute_confirmed", False),
        substitute_pending=presence.get("substitute_pending", False),
        is_substitute_assignment=is_substitute_assignment,
        can_self_checkin=presence["can_confirm_presence"],
        can_confirm_presence=presence["can_confirm_presence"],
        can_cancel_presence=presence["can_cancel_presence"],
        can_assign_substitute=presence["can_assign_substitute"],
        can_cancel_class=presence.get("can_cancel_class", False),
        can_uncancel_class=_can_uncancel_special(
            special=special,
            is_cancelled=is_cancelled,
            is_holiday_cancelled=bool(holiday),
        ),
    )


def _session_creation_defaults():
    now = timezone.now()
    return {
        "status": SessionStatus.SCHEDULED,
        "instructor_present": True,
        "instructor_checked_in_at": now,
    }


def _session_is_confirmed(session):
    if session is None:
        return True
    return session.instructor_present


def _special_is_confirmed(special):
    return special.instructor_present


def get_today_classes_for_person(person):
    today = timezone.localdate()
    weekday_code = PYTHON_WEEKDAY_TO_CODE[today.weekday()]

    enrollments = person.class_enrollments.filter(
        status="active",
    ).select_related("class_group")
    enrolled_group_ids = _training_class_group_ids(person)

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
    membership_pause = membership.current_pause if membership is not None else None
    membership_paused_until = membership_pause.requested_end_date if membership_pause else None

    def _special_entries():
        entries = []
        for sc in specials:
            checkin = special_checkins_by_special_id.get(sc.pk)
            is_cancelled, cancellation_reason = _special_cancel_state(sc, holiday)
            entries.append(SimpleNamespace(
                entry_role="student",
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
                is_cancelled=is_cancelled,
                cancellation_reason=cancellation_reason,
                instructor_present=sc.instructor_present and not sc.is_cancelled,
                has_checked_in=checkin is not None,
                checkin_id=checkin.pk if checkin else None,
                checkin_status=checkin.status if checkin else "",
                is_checkin_approved=bool(checkin and checkin.is_approved),
                can_cancel_checkin=bool(checkin and not checkin.is_approved),
                membership_paused=membership_pause is not None,
                membership_paused_until=membership_paused_until,
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
        is_cancelled = (session and session.is_cancelled) or bool(holiday)
        cancellation_reason = ""
        if holiday:
            cancellation_reason = holiday.name
        elif session and session.is_cancelled:
            cancellation_reason = session.cancellation_reason

        checkin = checkins_by_session_id.get(session.pk) if session else None

        result.append(SimpleNamespace(
            entry_role="student",
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
            instructor_present=_student_instructor_present(session),
            has_checked_in=checkin is not None,
            checkin_id=checkin.pk if checkin else None,
            checkin_status=checkin.status if checkin else "",
            is_checkin_approved=bool(checkin and checkin.is_approved),
            can_cancel_checkin=bool(checkin and not checkin.is_approved),
            membership_paused=membership_pause is not None,
            membership_paused_until=membership_paused_until,
        ))
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
        presence = _instructor_presence_state(
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
                checkins=[_instructor_checkin_view(c, is_special=False) for c in session_checkins],
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
                can_uncancel_class=_can_uncancel_class(
                    session=session,
                    is_cancelled=is_cancelled,
                    is_holiday_cancelled=bool(holiday),
                    is_original_instructor=is_original_instructor,
                ),
            )
        )

    special_classes = _instructor_special_classes_for_person(person, today)
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
        presence = _special_presence_state(special, viewer=person)
        entries.append(
            _build_instructor_special_entry(
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
            presence = _instructor_presence_state(
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
                checkins=[_instructor_checkin_view(c, is_special=False) for c in session_checkins],
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
                can_uncancel_class=_can_uncancel_class(
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
            is_cancelled = (session and session.is_cancelled) or bool(holiday)
            cancellation_reason = ""
            if holiday:
                cancellation_reason = holiday.name
            elif session and session.is_cancelled:
                cancellation_reason = session.cancellation_reason
            checkin = student_checkins_by_session.get(session.pk) if session else None
            entries.append(SimpleNamespace(
                entry_role="student",
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
                instructor_present=_student_instructor_present(session),
                has_checked_in=checkin is not None,
                checkin_id=checkin.pk if checkin else None,
                checkin_status=checkin.status if checkin else "",
                is_checkin_approved=bool(checkin and checkin.is_approved),
                can_cancel_checkin=bool(checkin and not checkin.is_approved),
            ))

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
            presence = _special_presence_state(special, viewer=person)
            entries.append(
                _build_instructor_special_entry(
                    special=special,
                    person=person,
                    today=today,
                    holiday=holiday,
                    checkins=special_class_checkins,
                    presence=presence,
                )
            )
        else:
            checkin = student_special_checkins_by_id.get(special.pk)
            is_cancelled, cancellation_reason = _special_cancel_state(special, holiday)
            entries.append(SimpleNamespace(
                entry_role="student",
                is_special=True,
                special_class=special,
                special_id=special.pk,
                schedule=None,
                session=None,
                class_group=None,
                start_time=special.start_time.strftime("%H:%M"),
                duration_minutes=special.duration_minutes,
                training_style="",
                teacher_name=special.teacher.full_name if special.teacher else "",
                category_name="Aulão",
                group_name=special.title,
                is_cancelled=is_cancelled,
                cancellation_reason=cancellation_reason,
                instructor_present=special.instructor_present and not special.is_cancelled,
                has_checked_in=checkin is not None,
                checkin_id=checkin.pk if checkin else None,
                checkin_status=checkin.status if checkin else "",
                is_checkin_approved=bool(checkin and checkin.is_approved),
                can_cancel_checkin=bool(checkin and not checkin.is_approved),
            ))

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
        is_cancelled = (session and session.is_cancelled) or bool(holiday)
        cancellation_reason = ""
        if holiday:
            cancellation_reason = holiday.name
        elif session and session.is_cancelled:
            cancellation_reason = session.cancellation_reason
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
        is_cancelled, cancellation_reason = _special_cancel_state(special, holiday)
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
                category_name="Aulão",
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


def _instructor_checkin_view(checkin, *, is_special):
    return SimpleNamespace(
        pk=checkin.pk,
        is_special=is_special,
        person_name=checkin.person.full_name,
        status=checkin.status,
        is_approved=checkin.is_approved,
        status_label=checkin.get_status_display(),
    )


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
        defaults=_session_creation_defaults(),
    )

    if not _can_instructor_access_session(instructor, schedule, session):
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

    if not _can_instructor_access_session(instructor, schedule, session):
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
def assign_session_substitute(instructor, schedule_id, substitute_teacher_id):
    today = timezone.localdate()
    schedule = assert_instructor_owns_schedule(instructor, schedule_id)
    session = (
        ClassSession.objects.filter(schedule=schedule, date=today)
        .select_related("substitute_teacher")
        .first()
    )
    if _session_is_confirmed(session):
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
    if _special_is_confirmed(special):
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
def register_instructor_self_special_checkin(instructor, special_id):
    special = SpecialClass.objects.select_related("substitute_teacher").get(pk=special_id)

    if not _can_instructor_access_special(instructor, special):
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

    if not _can_instructor_access_special(instructor, special):
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


def get_instructor_class_group_ids(person):
    cached = getattr(person, "_instructor_class_group_ids_cache", None)
    if cached is not None:
        return cached
    main_teacher_group_ids = set(
        ClassGroup.objects.filter(main_teacher=person, is_active=True).values_list("pk", flat=True)
    )
    assignment_group_ids = set(
        ClassInstructorAssignment.objects.filter(
            person=person,
            class_group__is_active=True,
        ).values_list("class_group_id", flat=True)
    )
    result = list(main_teacher_group_ids | assignment_group_ids)
    person._instructor_class_group_ids_cache = result
    return result


def assert_instructor_owns_schedule(person, schedule_id):
    schedule = ClassSchedule.objects.select_related("class_group").get(pk=schedule_id)
    if schedule.class_group_id not in get_instructor_class_group_ids(person):
        raise PermissionError("Você não é responsável por esta turma.")
    return schedule


def _can_instructor_access_session(person, schedule, session):
    if schedule.class_group_id in get_instructor_class_group_ids(person):
        return True
    return bool(session and session.substitute_teacher_id == person.pk)


def _can_instructor_access_special(person, special):
    if special.teacher_id == person.pk:
        return True
    return special.substitute_teacher_id == person.pk


def assert_instructor_owns_special(person, special_id):
    special = SpecialClass.objects.get(pk=special_id)
    if special.teacher_id != person.pk:
        raise PermissionError("Você não é responsável por este aulão.")
    return special


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

    membership = get_active_membership(person)
    if membership is not None and membership.is_currently_paused:
        pause = membership.current_pause
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
            is_cancelled, cancellation_reason = _special_cancel_state(sc, holiday)
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
        defaults=_session_creation_defaults(),
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
    now = timezone.now()
    special = SpecialClass.objects.create(
        title=title,
        date=date,
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


def _get_month_name(month):
    return date_format(date(2000, month, 1), "F")
