from system.business_rule.models import (
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    SpecialClass,
)



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


def can_instructor_access_session(person, schedule, session):
    if schedule.class_group_id in get_instructor_class_group_ids(person):
        return True
    return bool(session and session.substitute_teacher_id == person.pk)


def can_instructor_access_special(person, special):
    if special.teacher_id == person.pk:
        return True
    return special.substitute_teacher_id == person.pk


def assert_instructor_owns_special(person, special_id):
    special = SpecialClass.objects.get(pk=special_id)
    if special.teacher_id != person.pk:
        raise PermissionError("Você não é responsável por este aulão.")
    return special
