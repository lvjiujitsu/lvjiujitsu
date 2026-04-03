from django.db.models import Prefetch

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_PROFESSOR, ROLE_RECEPCAO
from system.models import (
    ClassGroup,
    GraduationExam,
    GraduationExamParticipation,
    GraduationHistory,
    GraduationRule,
    PhysicalAttendance,
    StudentProfile,
)


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


def get_graduation_rules_queryset():
    return GraduationRule.objects.select_related("discipline", "current_belt", "target_belt").order_by(
        "scope",
        "current_belt__display_order",
        "current_degree",
    )


def get_graduation_histories_queryset():
    return GraduationHistory.objects.select_related("student__user", "belt_rank", "recorded_by")


def get_graduation_exams_queryset():
    participations = GraduationExamParticipation.objects.select_related(
        "student__user",
        "current_belt",
        "suggested_belt",
        "decided_by",
        "promoted_history__belt_rank",
    ).order_by("student__user__full_name")
    return GraduationExam.objects.select_related("discipline", "class_group", "created_by").prefetch_related(
        Prefetch("participations", queryset=participations)
    )


def get_graduation_panel_class_groups_queryset(user):
    queryset = ClassGroup.objects.select_related("modality", "instructor__user", "reference_belt").filter(is_active=True)
    if user.has_any_role(*ADMIN_ROLE_CODES):
        return queryset.order_by("name")
    if user.has_role(ROLE_PROFESSOR):
        return queryset.filter(instructor__user=user).order_by("name")
    return queryset.none()


def get_graduation_panel_students_queryset(user, *, class_group=None):
    queryset = StudentProfile.objects.select_related("user").filter(is_active=True)
    queryset = queryset.exclude(operational_status=StudentProfile.STATUS_INACTIVE)
    if class_group is not None:
        queryset = queryset.filter(attendances__session__class_group=class_group)
    if user.has_any_role(*ADMIN_ROLE_CODES):
        return _prefetch_graduation_queryset(queryset.distinct(), class_group)
    if not user.has_role(ROLE_PROFESSOR):
        return queryset.none()
    if class_group is None:
        queryset = queryset.filter(attendances__session__class_group__in=get_graduation_panel_class_groups_queryset(user))
    else:
        queryset = queryset.filter(attendances__session__class_group__in=get_graduation_panel_class_groups_queryset(user))
    return _prefetch_graduation_queryset(queryset.distinct(), class_group)


def get_recent_graduation_exams_queryset():
    return get_graduation_exams_queryset().order_by("-scheduled_for", "-created_at")[:5]


def _prefetch_graduation_queryset(queryset, class_group):
    current_histories = GraduationHistory.objects.filter(is_current=True).select_related("belt_rank")
    attendances = PhysicalAttendance.objects.select_related("session", "session__class_group")
    return queryset.prefetch_related(
        Prefetch("graduation_histories", queryset=current_histories, to_attr="prefetched_current_graduation_history"),
        Prefetch("attendances", queryset=attendances.order_by("-checked_in_at"), to_attr="prefetched_attendances"),
        "enrollment_pauses",
    )
