from collections import OrderedDict
from system.business_rule.services.class_catalog import prepare_class_group_for_display
from system.business_rule.services.class_overview import build_class_group_filter_value
from system.business_rule.constants import (
    CLASS_ENROLLMENT_PERSON_TYPE_CODES,
    INSTRUCTOR_PERSON_TYPE_CODES,
)


def format_person_delete_blockers(protected_objects):
    labels = []
    label_by_model = {
        "ClassGroup": "turma principal",
        "SpecialClass": "aula especial",
        "TeacherPayout": "repasse financeiro",
    }
    for protected_object in protected_objects:
        label = label_by_model.get(
            protected_object.__class__.__name__,
            "vínculo protegido",
        )
        if label not in labels:
            labels.append(label)
    if not labels:
        return "vínculo protegido"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} e {labels[1]}"
    return f"{', '.join(labels[:-1])} e {labels[-1]}"


def hydrate_person_relationships(person, active_ibjjf_categories):
    active_enrollments = list(person.class_enrollments.all())
    student_relationships = _build_student_relationships(active_enrollments)
    person_type_code = person.person_type.code if person.person_type_id else ""
    person.active_group_labels = student_relationships["group_labels"]
    person.active_schedule_labels = student_relationships["schedule_labels"]
    person.active_schedule_sections = student_relationships["schedule_sections"]
    person.teaching_groups = _get_person_teaching_groups(person)
    person.teaching_group_labels = [
        class_group.catalog_title for class_group in person.teaching_groups
    ]
    person.teaching_schedule_labels = []
    for class_group in person.teaching_groups:
        for label in class_group.schedule_labels:
            if label not in person.teaching_schedule_labels:
                person.teaching_schedule_labels.append(label)
    person.teaching_schedule_sections = _build_grouped_schedule_sections(
        person.teaching_groups
    )
    person.resolved_ibjjf_category = next(
        (
            category
            for category in active_ibjjf_categories
            if person.get_age() is not None and category.matches_age(person.get_age())
        ),
        None,
    )
    person.show_student_context = bool(
        person_type_code in CLASS_ENROLLMENT_PERSON_TYPE_CODES
        or person.active_group_labels
    )
    person.show_teacher_context = bool(
        person_type_code in INSTRUCTOR_PERSON_TYPE_CODES
        or person.teaching_group_labels
    )


def _get_person_teaching_groups(person):
    teaching_groups = []
    seen_group_ids = set()
    for class_group in person.primary_class_groups.all():
        prepared_group = prepare_class_group_for_display(class_group)
        if prepared_group.pk in seen_group_ids:
            continue
        teaching_groups.append(prepared_group)
        seen_group_ids.add(prepared_group.pk)
    for assignment in person.class_instructor_assignments.all():
        prepared_group = prepare_class_group_for_display(assignment.class_group)
        if prepared_group.pk in seen_group_ids:
            continue
        teaching_groups.append(prepared_group)
        seen_group_ids.add(prepared_group.pk)
    return teaching_groups


def _build_student_relationships(active_enrollments):
    grouped_labels = OrderedDict()
    grouped_schedule_entries = OrderedDict()
    schedule_entries = OrderedDict()

    for enrollment in active_enrollments:
        class_group = enrollment.class_group
        group_key = build_class_group_filter_value(
            class_group.class_category_id,
            class_group.display_name,
        )
        if group_key not in grouped_labels:
            grouped_labels[group_key] = (
                f"{class_group.class_category.display_name} · {class_group.display_name}"
            )
        if group_key not in grouped_schedule_entries:
            grouped_schedule_entries[group_key] = OrderedDict()
        for schedule in class_group.schedules.all():
            schedule_key = (schedule.weekday, schedule.start_time.strftime("%H:%M"))
            schedule_label = (
                f"{schedule.get_weekday_display()} · {schedule.start_time.strftime('%H:%M')}"
            )
            weekday_label = schedule.get_weekday_display()
            time_label = schedule.start_time.strftime("%H:%M")
            if weekday_label not in grouped_schedule_entries[group_key]:
                grouped_schedule_entries[group_key][weekday_label] = []
            if time_label not in grouped_schedule_entries[group_key][weekday_label]:
                grouped_schedule_entries[group_key][weekday_label].append(time_label)
            if schedule_key in schedule_entries:
                continue
            schedule_entries[schedule_key] = schedule_label

    return {
        "group_labels": list(grouped_labels.values()),
        "schedule_labels": list(schedule_entries.values()),
        "schedule_sections": [
            {
                "group_label": grouped_labels[group_key],
                "schedule_labels": [
                    f"{weekday_label} · {time_label}"
                    for weekday_label, time_labels in grouped_schedule_entries[group_key].items()
                    for time_label in _sort_time_labels(time_labels)
                ],
                "schedule_count": sum(
                    len(time_labels)
                    for time_labels in grouped_schedule_entries[group_key].values()
                ),
                "weekday_sections": [
                    {
                        "weekday_label": weekday_label,
                        "time_labels": _sort_time_labels(time_labels),
                    }
                    for weekday_label, time_labels in grouped_schedule_entries[group_key].items()
                ],
            }
            for group_key in grouped_labels
        ],
    }


def _build_grouped_schedule_sections(class_groups):
    sections = []
    for class_group in class_groups:
        schedule_labels = []
        seen_labels = set()
        weekday_entries = OrderedDict()
        for label in class_group.schedule_labels:
            if label in seen_labels:
                continue
            schedule_labels.append(label)
            seen_labels.add(label)
        for schedule in class_group.schedule_cards:
            weekday_label = schedule.get_weekday_display()
            time_label = schedule.start_time.strftime("%H:%M")
            if weekday_label not in weekday_entries:
                weekday_entries[weekday_label] = []
            if time_label not in weekday_entries[weekday_label]:
                weekday_entries[weekday_label].append(time_label)
        sections.append(
            {
                "group_label": class_group.catalog_title,
                "schedule_labels": schedule_labels,
                "schedule_count": len(schedule_labels),
                "weekday_sections": [
                    {
                        "weekday_label": weekday_label,
                        "time_labels": _sort_time_labels(time_labels),
                    }
                    for weekday_label, time_labels in weekday_entries.items()
                ],
            }
        )
    return sections


def _sort_time_labels(time_labels):
    return sorted(
        time_labels,
        key=lambda value: tuple(int(part) for part in value.split(":", 1)),
    )


def compute_belt_stripes(graduation_progress):
    if graduation_progress is None or graduation_progress.current_belt_rank is None:
        return []
    belt = graduation_progress.current_belt_rank
    grade = graduation_progress.current_grade_number or 0
    slots = belt.get_grade_slots(grade)
    n = len(slots)
    if n == 0:
        return []
    tip_start, tip_width, stripe_w, stripe_gap = 232, 88, 12, 5
    total_w = n * stripe_w + (n - 1) * stripe_gap
    sx = tip_start + (tip_width - total_w) // 2
    return [{"filled": f, "x": sx + i * (stripe_w + stripe_gap)} for i, f in enumerate(slots)]
