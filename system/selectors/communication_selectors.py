from django.db.models import Q
from django.utils import timezone

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_PROFESSOR, ROLE_RECEPCAO
from system.models import (
    AUDIENCE_ACTIVE_HOUSEHOLDS,
    AUDIENCE_ACTIVE_STUDENTS,
    AUDIENCE_ALL_USERS,
    AUDIENCE_INSTRUCTORS,
    AUDIENCE_PENDING_FINANCIAL,
    AUDIENCE_STAFF,
    BulkCommunication,
    LocalSubscription,
    NoticeBoardMessage,
    StudentProfile,
    SystemUser,
)


def get_active_notice_board_messages_for_user(user):
    queryset = NoticeBoardMessage.objects.select_related("created_by")
    queryset = queryset.filter(is_active=True, starts_at__lte=timezone.now())
    queryset = queryset.filter(Q(ends_at__isnull=True) | Q(ends_at__gte=timezone.now()))
    audience_values = _get_user_audiences(user)
    return queryset.filter(audience__in=audience_values).order_by("-starts_at")


def get_communication_center_context():
    return {
        "notices": NoticeBoardMessage.objects.select_related("created_by").order_by("-starts_at", "-created_at"),
        "communications": BulkCommunication.objects.select_related("created_by").prefetch_related("deliveries"),
    }


def get_recipient_users_for_audience(audience):
    queryset = SystemUser.objects.filter(is_active=True)
    filters = _resolve_audience_filters(audience)
    return queryset.filter(filters).distinct()


def _get_user_audiences(user):
    audiences = {AUDIENCE_ALL_USERS}
    if user.has_any_role(ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO):
        audiences.add(AUDIENCE_STAFF)
    if user.has_role(ROLE_PROFESSOR):
        audiences.add(AUDIENCE_INSTRUCTORS)
    if _has_active_student_access(user):
        audiences.add(AUDIENCE_ACTIVE_STUDENTS)
    if _belongs_to_active_household(user):
        audiences.add(AUDIENCE_ACTIVE_HOUSEHOLDS)
    if _has_pending_financial_household(user):
        audiences.add(AUDIENCE_PENDING_FINANCIAL)
    return audiences


def _resolve_audience_filters(audience):
    mapping = {
        AUDIENCE_ALL_USERS: Q(),
        AUDIENCE_ACTIVE_STUDENTS: _active_students_q(),
        AUDIENCE_ACTIVE_HOUSEHOLDS: _active_households_q(),
        AUDIENCE_INSTRUCTORS: Q(roles__code=ROLE_PROFESSOR),
        AUDIENCE_STAFF: Q(roles__code__in=(ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)),
        AUDIENCE_PENDING_FINANCIAL: _pending_financial_q(),
    }
    return mapping[audience]


def _active_students_q():
    return Q(
        student_profile__operational_status=StudentProfile.STATUS_ACTIVE,
        student_profile__self_service_access=True,
    )


def _active_households_q():
    student_filter = Q(
        student_profile__operational_status=StudentProfile.STATUS_ACTIVE,
        student_profile__self_service_access=True,
    )
    guardian_filter = Q(
        dependent_links_as_responsible__student__operational_status=StudentProfile.STATUS_ACTIVE,
        dependent_links_as_responsible__end_date__isnull=True,
    )
    responsible_filter = Q(financial_subscriptions__covered_students__student__operational_status=StudentProfile.STATUS_ACTIVE)
    return student_filter | guardian_filter | responsible_filter


def _pending_financial_q():
    pending_statuses = (LocalSubscription.STATUS_PENDING_FINANCIAL, LocalSubscription.STATUS_BLOCKED)
    return Q(financial_subscriptions__status__in=pending_statuses)


def _has_active_student_access(user):
    queryset = StudentProfile.objects.filter(
        user=user,
        operational_status=StudentProfile.STATUS_ACTIVE,
        self_service_access=True,
    )
    return queryset.exists()


def _belongs_to_active_household(user):
    household_filter = _active_households_q()
    return SystemUser.objects.filter(pk=user.pk).filter(household_filter).exists()


def _has_pending_financial_household(user):
    filters = Q(financial_subscriptions__status__in=("PENDING_FINANCIAL", "BLOCKED"))
    return SystemUser.objects.filter(pk=user.pk).filter(filters).exists()
