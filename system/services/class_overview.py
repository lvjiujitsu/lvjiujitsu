from collections import OrderedDict
from types import SimpleNamespace

from system.services.class_catalog import (
    WEEKDAY_ORDER,
    get_admin_class_group_queryset,
    get_admin_class_schedule_queryset,
    get_info_class_group_queryset,
)


def build_class_group_filter_value(class_category_id, display_name):
    return f"{class_category_id}::{display_name}"


def parse_class_group_filter_value(value):
    if not value or "::" not in value:
        return None, None
    category_id, display_name = value.split("::", 1)
    try:
        return int(category_id), display_name
    except ValueError:
        return None, None


def get_public_class_group_cards():
    return _build_class_group_cards(get_info_class_group_queryset())


def get_admin_class_group_cards():
    return _build_class_group_cards(get_admin_class_group_queryset())


def get_class_group_card_by_pk(pk):
    class_groups = get_admin_class_group_queryset()
    target = _find_by_pk(class_groups, pk)
    if target is None:
        return None
    return _build_class_group_card(
        [
            class_group
            for class_group in class_groups
            if _get_class_group_key(class_group) == _get_class_group_key(target)
        ]
    )


def get_admin_schedule_day_cards():
    return _build_schedule_day_cards(get_admin_class_schedule_queryset())


def get_schedule_day_card_by_pk(pk):
    schedules = get_admin_class_schedule_queryset()
    target = _find_by_pk(schedules, pk)
    if target is None:
        return None
    return _build_schedule_day_card(
        [schedule for schedule in schedules if schedule.weekday == target.weekday]
    )


def get_class_group_filter_choices():
    return [
        (card.filter_value, card.catalog_title)
        for card in get_admin_class_group_cards()
    ]


def get_public_class_group_choice_options():
    return [
        (card.filter_value, card.catalog_title)
        for card in get_public_class_group_cards()
    ]


def resolve_class_group_selection(values, *, allow_inactive=False):
    if not values:
        return []

    class_group_cards = (
        get_admin_class_group_cards() if allow_inactive else get_public_class_group_cards()
    )
    logical_map = {
        card.filter_value: card.physical_groups for card in class_group_cards
    }
    physical_map = {
        str(class_group.pk): class_group
        for card in class_group_cards
        for class_group in card.physical_groups
    }
    resolved_groups = []
    for value in [str(item) for item in values if str(item)]:
        groups = logical_map.get(value)
        if groups is None:
            group = physical_map.get(value)
            groups = [group] if group else []
        for class_group in groups:
            if class_group and class_group not in resolved_groups:
                resolved_groups.append(class_group)
    return resolved_groups


def get_registration_catalog_payload():
    payload = []
    for card in get_public_class_group_cards():
        payload.append(
            {
                "id": card.filter_value,
                "code": card.filter_value,
                "display_name": card.display_name,
                "category_id": card.class_category.pk,
                "category_name": card.class_category.display_name,
                "category_audience": card.class_category.audience,
                "teacher_name": card.teaching_team[0]["full_name"] if card.teaching_team else "",
                "teacher_names": [member["full_name"] for member in card.teaching_team],
                "teacher_label": ", ".join(
                    member["full_name"] for member in card.teaching_team
                ) if card.teaching_team else "Equipe docente não definida",
                "schedules": [
                    {
                        "id": entry.pk,
                        "weekday": entry.weekday,
                        "weekday_display": entry.weekday_display,
                        "start_time": entry.time_label,
                    }
                    for entry in card.schedule_entries
                ],
            }
        )
    return payload


def get_weekday_filter_choices():
    return [
        (day_card.weekday, day_card.summary_label)
        for day_card in get_admin_schedule_day_cards()
    ]


def _build_class_group_cards(class_groups):
    grouped_map = OrderedDict()
    for class_group in class_groups:
        key = _get_class_group_key(class_group)
        if key not in grouped_map:
            grouped_map[key] = []
        grouped_map[key].append(class_group)
    return [_build_class_group_card(grouped_groups) for grouped_groups in grouped_map.values()]


def _build_class_group_card(class_groups):
    lead_group = class_groups[0]
    teaching_team_map = OrderedDict()
    schedule_entries = []

    for class_group in class_groups:
        for member in class_group.teaching_team:
            if member["id"] not in teaching_team_map:
                teaching_team_map[member["id"]] = member
        for schedule in class_group.schedule_cards:
            schedule_entries.append(
                SimpleNamespace(
                    pk=schedule.pk,
                    weekday=schedule.weekday,
                    weekday_display=schedule.get_weekday_display(),
                    time_label=schedule.time_label,
                    card_label=schedule.card_label,
                    training_style_display=schedule.get_training_style_display(),
                    duration_minutes=schedule.duration_minutes,
                    class_group_pk=class_group.pk,
                    class_group_title=class_group.catalog_title,
                    teacher_names=class_group.teaching_team_names,
                )
            )

    schedule_entries.sort(
        key=lambda entry: (
            WEEKDAY_ORDER.get(entry.weekday, 99),
            entry.time_label,
        )
    )
    return SimpleNamespace(
        pk=lead_group.pk,
        filter_value=build_class_group_filter_value(
            lead_group.class_category_id,
            lead_group.display_name,
        ),
        catalog_title=lead_group.catalog_title,
        public_title=f"{lead_group.display_name} · {lead_group.class_category.display_name}",
        display_name=lead_group.display_name,
        class_category=lead_group.class_category,
        team_count=len(teaching_team_map),
        teaching_team=list(teaching_team_map.values()),
        schedule_count=len(schedule_entries),
        schedule_entries=schedule_entries,
        schedule_day_summary=_build_schedule_day_summary(schedule_entries),
        physical_groups=class_groups,
        is_active=any(class_group.is_active for class_group in class_groups),
    )


def _build_schedule_day_cards(schedules):
    grouped_map = OrderedDict()
    for schedule in schedules:
        if schedule.weekday not in grouped_map:
            grouped_map[schedule.weekday] = []
        grouped_map[schedule.weekday].append(schedule)
    return [_build_schedule_day_card(day_schedules) for day_schedules in grouped_map.values()]


def _build_schedule_day_card(schedules):
    ordered_schedules = sorted(
        schedules,
        key=lambda schedule: (schedule.start_time, schedule.class_group_title),
    )
    lead_schedule = ordered_schedules[0]
    group_titles = list(OrderedDict.fromkeys(schedule.class_group_title for schedule in ordered_schedules))
    occurrences = [
        SimpleNamespace(
            pk=schedule.pk,
            time_label=schedule.start_time.strftime("%H:%M"),
            training_style_display=schedule.get_training_style_display(),
            duration_minutes=schedule.duration_minutes,
            class_group_title=schedule.class_group_title,
            category_title=schedule.category_title,
            teacher_names=schedule.linked_teacher_names,
            is_active=schedule.is_active,
        )
        for schedule in ordered_schedules
    ]
    return SimpleNamespace(
        pk=lead_schedule.pk,
        weekday=lead_schedule.weekday,
        title=lead_schedule.get_weekday_display(),
        summary_label=lead_schedule.get_weekday_display(),
        schedule_count=len(ordered_schedules),
        class_group_count=len(group_titles),
        group_titles=group_titles,
        occurrences=occurrences,
        is_active=any(schedule.is_active for schedule in ordered_schedules),
    )


def _build_schedule_day_summary(schedule_entries):
    grouped_map = OrderedDict()
    for entry in schedule_entries:
        if entry.weekday_display not in grouped_map:
            grouped_map[entry.weekday_display] = []
        if entry.time_label not in grouped_map[entry.weekday_display]:
            grouped_map[entry.weekday_display].append(entry.time_label)
    return [
        SimpleNamespace(
            weekday_label=weekday_label,
            time_labels=time_labels,
            summary_label=f"{weekday_label} · {', '.join(time_labels)}",
        )
        for weekday_label, time_labels in grouped_map.items()
    ]


def _get_class_group_key(class_group):
    return (class_group.class_category_id, class_group.display_name.casefold())


def _find_by_pk(items, pk):
    for item in items:
        if item.pk == pk:
            return item
    return None
