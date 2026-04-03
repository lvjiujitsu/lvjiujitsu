from system.models import ClassSession


def get_professor_sessions_queryset(user):
    queryset = ClassSession.objects.select_related("class_group", "class_group__instructor__user")
    return queryset.filter(class_group__instructor__user=user)
