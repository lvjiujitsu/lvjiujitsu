from django.db.models import Count, Prefetch

from system.models import ClassGroup, ClassSchedule, IbjjfAgeCategory


def get_admin_class_group_queryset():
    return (
        ClassGroup.objects.select_related(
            "class_category",
            "main_teacher",
        )
        .annotate(
            schedule_count=Count("schedules", distinct=True),
            assistant_count=Count("instructor_assignments", distinct=True),
            enrollment_count=Count("enrollments", distinct=True),
        )
        .order_by(
            "class_category__display_order",
            "class_category__display_name",
            "code",
        )
    )


def get_admin_class_schedule_queryset():
    return ClassSchedule.objects.select_related(
        "class_group",
        "class_group__class_category",
    ).order_by(
        "class_group__class_category__display_order",
        "class_group__class_category__display_name",
        "class_group__code",
        "display_order",
        "start_time",
    )


def get_info_class_group_queryset():
    active_schedule_queryset = ClassSchedule.objects.filter(is_active=True).order_by(
        "display_order",
        "start_time",
    )

    return (
        ClassGroup.objects.filter(is_active=True)
        .select_related("class_category", "main_teacher")
        .prefetch_related(
            Prefetch("schedules", queryset=active_schedule_queryset),
        )
        .order_by(
            "class_category__display_order",
            "class_category__display_name",
            "main_teacher__full_name",
            "code",
        )
    )


def get_registration_catalog_payload():
    class_groups = (
        ClassGroup.objects.filter(is_active=True)
        .select_related("class_category", "main_teacher")
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=ClassSchedule.objects.filter(is_active=True).order_by(
                    "display_order",
                    "start_time",
                ),
            )
        )
        .order_by("class_category__display_order", "code")
    )

    payload = []
    for class_group in class_groups:
        payload.append(
            {
                "id": class_group.pk,
                "code": class_group.code,
                "display_name": class_group.display_name,
                "category_id": class_group.class_category_id,
                "category_name": getattr(class_group.class_category, "display_name", ""),
                "category_audience": getattr(class_group.class_category, "audience", ""),
                "teacher_name": getattr(class_group.main_teacher, "full_name", ""),
                "schedules": [
                    {
                        "id": schedule.pk,
                        "weekday": schedule.weekday,
                        "weekday_display": schedule.get_weekday_display(),
                        "start_time": schedule.start_time.strftime("%H:%M"),
                    }
                    for schedule in class_group.schedules.all()
                ],
            }
        )
    return payload


def get_ibjjf_age_category_payload():
    return list(
        IbjjfAgeCategory.objects.filter(is_active=True)
        .order_by("display_order", "minimum_age")
        .values(
            "code",
            "display_name",
            "audience",
            "minimum_age",
            "maximum_age",
        )
    )
