from system.models import ClassDiscipline, ClassGroup, ClassSession, InstructorProfile


def get_instructor_profiles_queryset():
    return InstructorProfile.objects.select_related("user", "belt_rank").order_by("user__full_name")


def get_class_disciplines_queryset():
    return ClassDiscipline.objects.order_by("name")


def get_class_groups_queryset():
    return ClassGroup.objects.select_related("modality", "instructor__user", "reference_belt")


def get_class_sessions_queryset():
    return ClassSession.objects.select_related("class_group", "class_group__modality", "class_group__instructor__user")
