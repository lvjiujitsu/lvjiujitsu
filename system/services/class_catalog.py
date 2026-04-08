from collections import OrderedDict

from django.db.models import Prefetch

from system.models import (
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    IbjjfAgeCategory,
)


WEEKDAY_ORDER = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}


def get_admin_class_group_queryset():
    queryset = (
        ClassGroup.objects.select_related("class_category", "main_teacher")
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=_get_schedule_queryset(active_only=True),
            ),
            Prefetch(
                "instructor_assignments",
                queryset=_get_assignment_queryset(),
            ),
        )
        .order_by(
            "class_category__display_order",
            "class_category__display_name",
            "code",
        )
    )
    return [_prepare_class_group(class_group) for class_group in queryset]


def get_admin_class_schedule_queryset():
    queryset = (
        ClassSchedule.objects.select_related(
            "class_group",
            "class_group__class_category",
            "class_group__main_teacher",
        )
        .prefetch_related(
            Prefetch(
                "class_group__schedules",
                queryset=_get_schedule_queryset(active_only=True),
            ),
            Prefetch(
                "class_group__instructor_assignments",
                queryset=_get_assignment_queryset(),
            )
        )
        .order_by(
            "class_group__class_category__display_order",
            "class_group__class_category__display_name",
            "class_group__code",
            "weekday",
            "start_time",
        )
    )
    schedules = list(queryset)
    for schedule in schedules:
        class_group = _prepare_class_group(schedule.class_group)
        schedule.card_title = _build_schedule_label(schedule)
        schedule.class_group_title = class_group.catalog_title
        schedule.linked_teachers = class_group.teaching_team
        schedule.linked_teacher_names = class_group.teaching_team_names
        schedule.category_title = class_group.class_category.display_name
    return schedules


def get_info_catalog_context():
    class_groups = get_info_class_group_queryset()
    return {
        "category_sections": _build_category_sections(class_groups),
        "teacher_sections": _build_teacher_sections(class_groups),
        "schedule_sections": _build_schedule_sections(class_groups),
    }


def get_info_class_group_queryset():
    queryset = (
        ClassGroup.objects.filter(is_active=True)
        .select_related("class_category", "main_teacher")
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=_get_schedule_queryset(active_only=True),
            ),
            Prefetch(
                "instructor_assignments",
                queryset=_get_assignment_queryset(),
            ),
        )
        .order_by(
            "class_category__display_order",
            "class_category__display_name",
            "main_teacher__full_name",
            "code",
        )
    )
    return [_prepare_class_group(class_group) for class_group in queryset]


def get_registration_catalog_payload():
    class_groups = (
        ClassGroup.objects.filter(is_active=True)
        .select_related("class_category", "main_teacher")
        .prefetch_related(
            Prefetch(
                "schedules",
                queryset=_get_schedule_queryset(active_only=True),
            ),
            Prefetch(
                "instructor_assignments",
                queryset=_get_assignment_queryset(),
            ),
        )
        .order_by("class_category__display_order", "code")
    )

    payload = []
    for class_group in class_groups:
        prepared_group = _prepare_class_group(class_group)
        payload.append(
            {
                "id": prepared_group.pk,
                "code": prepared_group.code,
                "display_name": prepared_group.display_name,
                "category_id": prepared_group.class_category_id,
                "category_name": prepared_group.class_category.display_name,
                "category_audience": prepared_group.class_category.audience,
                "teacher_name": getattr(prepared_group.main_teacher, "full_name", ""),
                "teacher_names": prepared_group.teaching_team_names,
                "teacher_label": prepared_group.team_summary,
                "schedules": [
                    {
                        "id": schedule.pk,
                        "weekday": schedule.weekday,
                        "weekday_display": schedule.get_weekday_display(),
                        "start_time": schedule.start_time.strftime("%H:%M"),
                    }
                    for schedule in prepared_group.schedule_cards
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


def prepare_class_group_for_display(class_group):
    return _prepare_class_group(class_group)


def build_schedule_day_summary(class_group):
    prepared_group = _prepare_class_group(class_group)
    grouped_schedule_map = OrderedDict()

    for schedule in prepared_group.schedule_cards:
        weekday_label = schedule.get_weekday_display()
        if weekday_label not in grouped_schedule_map:
            grouped_schedule_map[weekday_label] = []
        grouped_schedule_map[weekday_label].append(schedule.start_time.strftime("%H:%M"))

    return [
        {
            "weekday_label": weekday_label,
            "time_labels": time_labels,
            "summary_label": f"{weekday_label} · {', '.join(time_labels)}",
        }
        for weekday_label, time_labels in grouped_schedule_map.items()
    ]


def _get_schedule_queryset(*, active_only):
    queryset = ClassSchedule.objects.order_by("weekday", "start_time")
    if active_only:
        queryset = queryset.filter(is_active=True)
    return queryset


def _get_assignment_queryset():
    return ClassInstructorAssignment.objects.select_related("person").order_by(
        "person__full_name"
    )


def _prepare_class_group(class_group):
    if getattr(class_group, "_catalog_prepared", False):
        return class_group

    class_group.schedule_cards = _prepare_schedule_cards(class_group)
    class_group.schedule_labels = [
        schedule.card_label for schedule in class_group.schedule_cards
    ]
    class_group.schedule_count = len(class_group.schedule_cards)
    class_group.catalog_title = (
        f"{class_group.class_category.display_name} · {class_group.display_name}"
    )
    class_group.teaching_team = _prepare_teaching_team(class_group)
    class_group.teaching_team_names = [
        member["full_name"] for member in class_group.teaching_team
    ]
    class_group.team_summary = (
        ", ".join(class_group.teaching_team_names)
        if class_group.teaching_team_names
        else "Equipe docente não definida"
    )
    class_group.team_count = len(class_group.teaching_team)
    class_group._catalog_prepared = True
    return class_group


def _prepare_schedule_cards(class_group):
    schedules = []
    for schedule in class_group.schedules.all():
        schedule.card_label = _build_schedule_label(schedule)
        schedule.time_label = schedule.start_time.strftime("%H:%M")
        schedule.weekday_position = WEEKDAY_ORDER.get(schedule.weekday, 99)
        schedules.append(schedule)
    schedules.sort(key=lambda item: (item.weekday_position, item.start_time))
    return schedules


def _prepare_teaching_team(class_group):
    members = []
    seen_person_ids = set()

    if class_group.main_teacher_id:
        members.append(
            {
                "id": class_group.main_teacher.pk,
                "full_name": class_group.main_teacher.full_name,
                "role_label": "Professor principal",
            }
        )
        seen_person_ids.add(class_group.main_teacher_id)

    for assignment in class_group.instructor_assignments.all():
        if assignment.person_id in seen_person_ids:
            continue
        members.append(
            {
                "id": assignment.person.pk,
                "full_name": assignment.person.full_name,
                "role_label": "Equipe auxiliar",
            }
        )
        seen_person_ids.add(assignment.person_id)

    return members


def _build_category_sections(class_groups):
    sections = OrderedDict()
    for class_group in class_groups:
        category = class_group.class_category
        if category.pk not in sections:
            sections[category.pk] = {
                "display_name": category.display_name,
                "description": category.description,
                "class_groups": [],
            }
        sections[category.pk]["class_groups"].append(class_group)
    return list(sections.values())


def _build_teacher_sections(class_groups):
    teacher_map = OrderedDict()
    for class_group in class_groups:
        for member in class_group.teaching_team:
            teacher_key = member["id"]
            if teacher_key not in teacher_map:
                teacher_map[teacher_key] = {
                    "display_name": member["full_name"],
                    "role_label": member["role_label"],
                    "class_groups": [],
                    "schedule_labels": [],
                    "_group_ids": set(),
                    "_schedule_labels": set(),
                }

            section = teacher_map[teacher_key]
            if class_group.pk not in section["_group_ids"]:
                section["class_groups"].append(class_group)
                section["_group_ids"].add(class_group.pk)

            for label in class_group.schedule_labels:
                if label not in section["_schedule_labels"]:
                    section["schedule_labels"].append(label)
                    section["_schedule_labels"].add(label)

    sections = list(teacher_map.values())
    for section in sections:
        section["schedule_labels"].sort(key=_schedule_label_sort_key)
        section.pop("_group_ids", None)
        section.pop("_schedule_labels", None)
    sections.sort(key=lambda item: item["display_name"])
    return sections


def _build_schedule_sections(class_groups):
    schedule_map = OrderedDict()
    for class_group in class_groups:
        for schedule in class_group.schedule_cards:
            schedule_key = (
                schedule.weekday,
                schedule.start_time,
                schedule.training_style,
            )
            if schedule_key not in schedule_map:
                schedule_map[schedule_key] = {
                    "label": schedule.card_label,
                    "weekday_position": schedule.weekday_position,
                    "start_time": schedule.start_time,
                    "groups": [],
                }
            schedule_map[schedule_key]["groups"].append(class_group)

    sections = list(schedule_map.values())
    sections.sort(
        key=lambda item: (
            item["weekday_position"],
            item["start_time"],
        )
    )
    return sections


def _build_schedule_label(schedule):
    return f"{schedule.get_weekday_display()} · {schedule.start_time.strftime('%H:%M')}"


def _schedule_label_sort_key(label):
    weekday_name = label.split(" · ", 1)[0]
    weekday_position = {
        "Segunda-feira": 1,
        "Terça-feira": 2,
        "Quarta-feira": 3,
        "Quinta-feira": 4,
        "Sexta-feira": 5,
        "Sábado": 6,
        "Domingo": 7,
    }.get(weekday_name, 99)
    return (weekday_position, label)
