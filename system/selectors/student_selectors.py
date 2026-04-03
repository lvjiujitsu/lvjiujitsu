from django.db.models import Prefetch, Q

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.models import GuardianRelationship, StudentProfile


def get_student_management_queryset(filters=None):
    queryset = StudentProfile.objects.select_related("user")
    queryset = queryset.prefetch_related(_guardian_prefetch())
    return _apply_student_filters(queryset, filters or {})


def _guardian_prefetch():
    queryset = GuardianRelationship.objects.select_related("responsible_user")
    return Prefetch("guardian_links", queryset=queryset.order_by("-is_primary", "-created_at"))


def _apply_student_filters(queryset, filters):
    if filters.get("name"):
        queryset = queryset.filter(user__full_name__icontains=filters["name"])
    if filters.get("cpf"):
        queryset = queryset.filter(user__cpf__icontains=filters["cpf"])
    if filters.get("status"):
        queryset = queryset.filter(operational_status=filters["status"])
    if filters.get("responsible"):
        queryset = queryset.filter(guardian_links__responsible_user__full_name__icontains=filters["responsible"])
    return queryset.distinct()


def get_visible_students_for_user(user):
    queryset = StudentProfile.objects.select_related("user").prefetch_related(_guardian_prefetch())
    if _is_staff_operator(user):
        return queryset
    return queryset.filter(_household_visibility_q(user)).distinct()


def _household_visibility_q(user):
    return (
        Q(user=user)
        | Q(guardian_links__responsible_user=user, guardian_links__end_date__isnull=True)
        | Q(subscription_links__subscription__responsible_user=user, subscription_links__is_active=True)
    )


def _is_staff_operator(user):
    return user.is_superuser or user.has_any_role(
        ROLE_ADMIN_MASTER,
        ROLE_ADMIN_UNIDADE,
        ROLE_RECEPCAO,
    )
