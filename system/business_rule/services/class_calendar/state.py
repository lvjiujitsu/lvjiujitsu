from datetime import date
from types import SimpleNamespace
from django.db.models import Q
from django.utils.formats import date_format
from django.utils import timezone
from system.business_rule.models import SpecialClass, WeekdayCode
from system.business_rule.models.calendar import SessionStatus


PYTHON_WEEKDAY_TO_CODE = {
    0: WeekdayCode.MONDAY,
    1: WeekdayCode.TUESDAY,
    2: WeekdayCode.WEDNESDAY,
    3: WeekdayCode.THURSDAY,
    4: WeekdayCode.FRIDAY,
    5: WeekdayCode.SATURDAY,
    6: WeekdayCode.SUNDAY,
}


def student_instructor_present(session):
    if session is None:
        return True
    return session.instructor_present


def training_class_group_ids(person):
    enrolled_group_ids = list(
        person.class_enrollments.filter(status="active").values_list(
            "class_group_id", flat=True
        )
    )
    if person.class_group_id and person.class_group_id not in enrolled_group_ids:
        enrolled_group_ids.append(person.class_group_id)
    return enrolled_group_ids


def instructor_presence_state(session, *, viewer, is_original_instructor, substitute_teacher):
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


def can_uncancel_class(*, session, is_cancelled, is_holiday_cancelled, is_original_instructor):
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


def special_cancel_state(special, holiday):
    is_cancelled = (special and special.is_cancelled) or bool(holiday)
    cancellation_reason = ""
    if holiday:
        cancellation_reason = holiday.name
    elif special and special.is_cancelled:
        cancellation_reason = special.cancellation_reason
    return is_cancelled, cancellation_reason


def special_presence_state(special, *, viewer):
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
    return instructor_presence_state(
        special,
        viewer=viewer,
        is_original_instructor=is_original_instructor,
        substitute_teacher=special.substitute_teacher,
    )


def instructor_special_classes_for_person(person, today):
    return list(
        SpecialClass.objects.filter(date=today)
        .filter(Q(teacher=person) | Q(substitute_teacher=person))
        .select_related("teacher", "substitute_teacher")
        .order_by("start_time")
    )


def build_instructor_special_entry(*, special, person, today, holiday, checkins, presence):
    is_cancelled, cancellation_reason = special_cancel_state(special, holiday)
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
        checkins=[instructor_checkin_view(c, is_special=True) for c in checkins],
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


def session_creation_defaults():
    now = timezone.now()
    return {
        "status": SessionStatus.SCHEDULED,
        "instructor_present": True,
        "instructor_checked_in_at": now,
    }


def session_is_confirmed(session):
    if session is None:
        return True
    return session.instructor_present


def special_is_confirmed(special):
    return special.instructor_present


def instructor_checkin_view(checkin, *, is_special):
    return SimpleNamespace(
        pk=checkin.pk,
        is_special=is_special,
        person_name=checkin.person.full_name,
        status=checkin.status,
        is_approved=checkin.is_approved,
        status_label=checkin.get_status_display(),
    )


def get_month_name(month):
    return date_format(date(2000, month, 1), "F")


SPECIAL_CATEGORY_NAME = "Aulão"


def session_cancellation(session, holiday):
    if holiday:
        return True, holiday.name
    if session and session.is_cancelled:
        return True, session.cancellation_reason
    return False, ""


def student_session_entry(schedule, session, checkin, holiday, *, pause=None, paused_until=None):
    is_cancelled, cancellation_reason = session_cancellation(session, holiday)
    class_group = schedule.class_group
    return SimpleNamespace(
        entry_role="student",
        is_special=False,
        special_class=None,
        special_id=None,
        schedule=schedule,
        session=session,
        class_group=class_group,
        start_time=schedule.start_time.strftime("%H:%M"),
        duration_minutes=schedule.duration_minutes,
        training_style=schedule.get_training_style_display(),
        teacher_name=class_group.main_teacher.full_name if class_group.main_teacher else "",
        category_name=class_group.class_category.display_name,
        group_name=class_group.display_name,
        is_cancelled=is_cancelled,
        cancellation_reason=cancellation_reason,
        instructor_present=student_instructor_present(session),
        has_checked_in=checkin is not None,
        checkin_id=checkin.pk if checkin else None,
        checkin_status=checkin.status if checkin else "",
        is_checkin_approved=bool(checkin and checkin.is_approved),
        can_cancel_checkin=bool(checkin and not checkin.is_approved),
        membership_paused=pause is not None,
        membership_paused_until=paused_until,
    )


def student_special_entry(special, checkin, holiday, *, pause=None, paused_until=None):
    is_cancelled, cancellation_reason = special_cancel_state(special, holiday)
    return SimpleNamespace(
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
        category_name=SPECIAL_CATEGORY_NAME,
        group_name=special.title,
        is_cancelled=is_cancelled,
        cancellation_reason=cancellation_reason,
        instructor_present=special.instructor_present and not special.is_cancelled,
        has_checked_in=checkin is not None,
        checkin_id=checkin.pk if checkin else None,
        checkin_status=checkin.status if checkin else "",
        is_checkin_approved=bool(checkin and checkin.is_approved),
        can_cancel_checkin=bool(checkin and not checkin.is_approved),
        membership_paused=pause is not None,
        membership_paused_until=paused_until,
    )
