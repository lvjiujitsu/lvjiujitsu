from django.db.models import Prefetch, Q

from system.models import (
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
)
from system.services.class_overview import parse_class_group_filter_value
from system.constants import PersonTypeCode


def get_person_queryset(*, filters=None):
    queryset = (
        Person.objects.select_related(
            "access_account",
            "person_type",
            "class_category",
            "class_group",
            "class_schedule",
        )
        .prefetch_related(
            Prefetch(
                "class_enrollments",
                queryset=ClassEnrollment.objects.select_related(
                    "class_group",
                    "class_group__class_category",
                )
                .prefetch_related(
                    Prefetch(
                        "class_group__schedules",
                        queryset=ClassSchedule.objects.filter(is_active=True).order_by(
                            "weekday",
                            "start_time",
                        ),
                    ),
                )
                .filter(status="active"),
            ),
            Prefetch(
                "primary_class_groups",
                queryset=ClassGroup.objects.select_related(
                    "class_category",
                    "main_teacher",
                ).prefetch_related(
                    Prefetch(
                        "schedules",
                        queryset=ClassSchedule.objects.filter(is_active=True).order_by(
                            "weekday",
                            "start_time",
                        ),
                    ),
                    Prefetch(
                        "instructor_assignments",
                        queryset=ClassInstructorAssignment.objects.select_related(
                            "person"
                        ).order_by("person__full_name"),
                    ),
                ),
            ),
            Prefetch(
                "class_instructor_assignments",
                queryset=ClassInstructorAssignment.objects.select_related(
                    "class_group",
                    "class_group__class_category",
                    "class_group__main_teacher",
                ).prefetch_related(
                    Prefetch(
                        "class_group__schedules",
                        queryset=ClassSchedule.objects.filter(is_active=True).order_by(
                            "weekday",
                            "start_time",
                        ),
                    ),
                    Prefetch(
                        "class_group__instructor_assignments",
                        queryset=ClassInstructorAssignment.objects.select_related(
                            "person"
                        ).order_by("person__full_name"),
                    ),
                ),
            ),
        )
        .order_by("full_name")
    )
    if not filters:
        return queryset
    return _apply_filters(queryset, filters)


def _apply_filters(queryset, filters):
    full_name = filters.get("full_name")
    cpf = filters.get("cpf")
    class_category = filters.get("class_category")
    class_group_key = filters.get("class_group_key")
    weekday = filters.get("weekday")

    if full_name:
        queryset = queryset.filter(full_name__icontains=full_name)
    if cpf:
        queryset = queryset.filter(cpf__icontains=cpf)
    if filters.get("is_teacher"):
        queryset = queryset.filter(
            Q(person_type__code=PersonTypeCode.INSTRUCTOR)
            | Q(primary_class_groups__isnull=False)
            | Q(class_instructor_assignments__isnull=False)
        )
    if class_category:
        queryset = queryset.filter(
            Q(class_category=class_category)
            | Q(class_group__class_category=class_category)
            | Q(class_enrollments__status="active", class_enrollments__class_group__class_category=class_category)
            | Q(primary_class_groups__class_category=class_category)
            | Q(class_instructor_assignments__class_group__class_category=class_category)
        )
    if class_group_key:
        category_id, display_name = parse_class_group_filter_value(class_group_key)
        if category_id and display_name:
            queryset = queryset.filter(
                Q(class_group__class_category_id=category_id, class_group__display_name=display_name)
                | Q(class_enrollments__status="active", class_enrollments__class_group__class_category_id=category_id, class_enrollments__class_group__display_name=display_name)
                | Q(primary_class_groups__class_category_id=category_id, primary_class_groups__display_name=display_name)
                | Q(class_instructor_assignments__class_group__class_category_id=category_id, class_instructor_assignments__class_group__display_name=display_name)
            )
    if weekday:
        queryset = queryset.filter(
            Q(class_schedule__weekday=weekday)
            | Q(class_group__schedules__weekday=weekday, class_group__schedules__is_active=True)
            | Q(class_enrollments__status="active", class_enrollments__class_group__schedules__weekday=weekday, class_enrollments__class_group__schedules__is_active=True)
            | Q(primary_class_groups__schedules__weekday=weekday, primary_class_groups__schedules__is_active=True)
            | Q(class_instructor_assignments__class_group__schedules__weekday=weekday, class_instructor_assignments__class_group__schedules__is_active=True)
        )
    return queryset.distinct()
