from collections import defaultdict
from datetime import date, timedelta
from types import SimpleNamespace

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from system.business_rule.models import (
    BeltRank,
    Graduation,
    GraduationRule,
)
from system.business_rule.models.calendar import (
    CheckinStatus,
    ClassCheckin,
    SessionStatus,
    SpecialClassCheckin,
)


def count_approved_classes_in_window(person, start_date, end_date):
    if start_date is None or end_date is None or end_date < start_date:
        return 0
    regular_dates = set(
        ClassCheckin.objects.filter(
            person=person,
            status=CheckinStatus.APPROVED,
            session__date__gte=start_date,
            session__date__lte=end_date,
        )
        .exclude(session__status=SessionStatus.CANCELLED)
        .values_list("session__date", flat=True)
    )
    special_dates = set(
        SpecialClassCheckin.objects.filter(
            person=person,
            status=CheckinStatus.APPROVED,
            special_class__date__gte=start_date,
            special_class__date__lte=end_date,
        )
        .exclude(special_class__status=SessionStatus.CANCELLED)
        .values_list("special_class__date", flat=True)
    )
    return len(regular_dates | special_dates)


def get_current_graduation(person):
    real_graduation = (
        Graduation.objects.filter(person=person)
        .select_related("belt_rank")
        .order_by("-awarded_at", "-created_at")
        .first()
    )
    if real_graduation is not None:
        return real_graduation
    return _legacy_graduation_from_person(person)


def get_initial_belt_rank_for_age(age):
    if age is None:
        return None
    return (
        BeltRank.objects.filter(is_active=True)
        .filter(Q(min_age__isnull=True) | Q(min_age__lte=age))
        .filter(Q(max_age__isnull=True) | Q(max_age__gte=age))
        .order_by("display_order", "display_name")
        .first()
    )


def get_initial_belt_rank_for_person(person, reference_date=None):
    return get_initial_belt_rank_for_age(person.get_age(reference_date))


def _legacy_graduation_from_person(person):
    legacy_code = (person.jiu_jitsu_belt or "").strip()
    if not legacy_code:
        return None
    belt_rank = BeltRank.objects.filter(code=legacy_code).first()
    if belt_rank is None:
        return None
    return SimpleNamespace(
        person=person,
        belt_rank=belt_rank,
        grade_number=person.jiu_jitsu_stripes or 0,
        awarded_at=person.created_at.date() if person.created_at else timezone.localdate(),
        awarded_by=None,
        notes="Migrado dos campos legados de cadastro.",
        pk=None,
    )


def _resolve_applicable_rule(belt_rank, grade_number):
    return (
        GraduationRule.objects.filter(
            belt_rank=belt_rank,
            from_grade=grade_number,
            is_active=True,
        )
        .first()
    )


def _months_between(start_date, end_date):
    if start_date is None or end_date is None or end_date < start_date:
        return 0
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day < start_date.day:
        months -= 1
    return max(0, months)


def add_months(reference_date, months):
    total_month = reference_date.month - 1 + months
    year = reference_date.year + total_month // 12
    month = total_month % 12 + 1
    day = min(reference_date.day, _last_day_of_month(year, month))
    return date(year, month, day)


def _last_day_of_month(year, month):
    if month == 12:
        return 31
    next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def compute_graduation_progress(person, reference_date=None):
    reference_date = reference_date or timezone.localdate()
    current = get_current_graduation(person)
    if current is None:
        return SimpleNamespace(
            person=person,
            current_belt_rank=None,
            current_grade_number=None,
            current_graduation_date=None,
            applicable_rule=None,
            target_belt_rank=None,
            target_grade_number=None,
            months_in_current_grade=0,
            required_months=0,
            months_remaining=0,
            approved_classes_in_window=0,
            required_classes=0,
            missing_classes=0,
            window_start=None,
            window_end=reference_date,
            is_eligible=False,
            progress_pct=0.0,
            blocker="Sem registro de graduação.",
        )

    rule = _resolve_applicable_rule(current.belt_rank, current.grade_number)
    months_in_current_grade = _months_between(current.awarded_at, reference_date)

    if rule is None:
        return SimpleNamespace(
            person=person,
            current_belt_rank=current.belt_rank,
            current_grade_number=current.grade_number,
            current_graduation_date=current.awarded_at,
            applicable_rule=None,
            target_belt_rank=None,
            target_grade_number=None,
            months_in_current_grade=months_in_current_grade,
            required_months=0,
            months_remaining=0,
            approved_classes_in_window=0,
            required_classes=0,
            missing_classes=0,
            window_start=None,
            window_end=reference_date,
            is_eligible=False,
            progress_pct=0.0,
            blocker="Sem regra de graduação cadastrada para esta faixa/grau.",
        )

    if rule.min_classes_window_months and rule.min_classes_window_months > 0:
        window_start = add_months(reference_date, -rule.min_classes_window_months)
    else:
        window_start = current.awarded_at

    approved_classes = count_approved_classes_in_window(person, window_start, reference_date)
    required_classes = rule.min_classes_required
    missing_classes = max(0, required_classes - approved_classes)
    required_months = rule.min_months_in_current_grade
    months_remaining = max(0, required_months - months_in_current_grade)

    if rule.promotes_to_next_rank:
        target_belt_rank = current.belt_rank.next_rank
        target_grade_number = 0
    else:
        target_belt_rank = current.belt_rank
        target_grade_number = rule.to_grade

    age = person.get_age(reference_date)
    age_blocker = ""
    if target_belt_rank is not None and target_belt_rank.min_age and age is not None:
        if age < target_belt_rank.min_age:
            age_blocker = (
                f"Idade mínima da faixa {target_belt_rank.display_name}: "
                f"{target_belt_rank.min_age} anos."
            )

    is_eligible = (
        months_remaining == 0
        and missing_classes == 0
        and target_belt_rank is not None
        and not age_blocker
    )

    progress_pct = _compute_progress_pct(
        months_in_current_grade=months_in_current_grade,
        required_months=required_months,
        approved_classes=approved_classes,
        required_classes=required_classes,
    )

    return SimpleNamespace(
        person=person,
        current_belt_rank=current.belt_rank,
        current_grade_number=current.grade_number,
        current_graduation_date=current.awarded_at,
        applicable_rule=rule,
        target_belt_rank=target_belt_rank,
        target_grade_number=target_grade_number,
        months_in_current_grade=months_in_current_grade,
        required_months=required_months,
        months_remaining=months_remaining,
        approved_classes_in_window=approved_classes,
        required_classes=required_classes,
        missing_classes=missing_classes,
        window_start=window_start,
        window_end=reference_date,
        is_eligible=is_eligible,
        progress_pct=progress_pct,
        blocker=age_blocker,
    )


def _empty_progress(person, reference_date, blocker, *, current=None, months_in_current_grade=0):
    return SimpleNamespace(
        person=person,
        current_belt_rank=current.belt_rank if current is not None else None,
        current_grade_number=current.grade_number if current is not None else None,
        current_graduation_date=current.awarded_at if current is not None else None,
        applicable_rule=None,
        target_belt_rank=None,
        target_grade_number=None,
        months_in_current_grade=months_in_current_grade,
        required_months=0,
        months_remaining=0,
        approved_classes_in_window=0,
        required_classes=0,
        missing_classes=0,
        window_start=None,
        window_end=reference_date,
        is_eligible=False,
        progress_pct=0.0,
        blocker=blocker,
    )


def compute_graduation_progress_bulk(persons, reference_date=None):
    reference_date = reference_date or timezone.localdate()
    persons = list(persons)
    if not persons:
        return {}

    person_by_id = {person.pk: person for person in persons}

    current_by_person = {}
    graduations = (
        Graduation.objects.filter(person_id__in=person_by_id.keys())
        .select_related("belt_rank")
        .order_by("person_id", "-awarded_at", "-created_at")
    )
    for graduation in graduations:
        current_by_person.setdefault(graduation.person_id, graduation)

    missing_ids = [pid for pid in person_by_id if pid not in current_by_person]
    if missing_ids:
        legacy_codes = {
            person_by_id[pid].jiu_jitsu_belt.strip()
            for pid in missing_ids
            if (person_by_id[pid].jiu_jitsu_belt or "").strip()
        }
        belt_ranks_by_code = (
            {belt_rank.code: belt_rank for belt_rank in BeltRank.objects.filter(code__in=legacy_codes)}
            if legacy_codes
            else {}
        )
        for pid in missing_ids:
            person = person_by_id[pid]
            legacy_code = (person.jiu_jitsu_belt or "").strip()
            belt_rank = belt_ranks_by_code.get(legacy_code) if legacy_code else None
            if belt_rank is None:
                continue
            current_by_person[pid] = SimpleNamespace(
                person=person,
                belt_rank=belt_rank,
                grade_number=person.jiu_jitsu_stripes or 0,
                awarded_at=person.created_at.date() if person.created_at else reference_date,
                awarded_by=None,
                notes="Migrado dos campos legados de cadastro.",
                pk=None,
            )

    rules_by_key = {}
    for rule in GraduationRule.objects.filter(is_active=True):
        rules_by_key.setdefault((rule.belt_rank_id, rule.from_grade), rule)

    windows = {}
    for pid, current in current_by_person.items():
        rule = rules_by_key.get((current.belt_rank.pk, current.grade_number))
        if rule is None:
            continue
        if rule.min_classes_window_months and rule.min_classes_window_months > 0:
            window_start = add_months(reference_date, -rule.min_classes_window_months)
        else:
            window_start = current.awarded_at
        windows[pid] = (window_start, reference_date)

    approved_dates = defaultdict(set)
    if windows:
        global_start = min(window_start for window_start, _ in windows.values())
        person_ids_with_window = list(windows.keys())

        regular_checkins = (
            ClassCheckin.objects.filter(
                person_id__in=person_ids_with_window,
                status=CheckinStatus.APPROVED,
                session__date__gte=global_start,
                session__date__lte=reference_date,
            )
            .exclude(session__status=SessionStatus.CANCELLED)
            .values_list("person_id", "session__date")
        )
        for person_id, checkin_date in regular_checkins:
            approved_dates[person_id].add(checkin_date)

        special_checkins = (
            SpecialClassCheckin.objects.filter(
                person_id__in=person_ids_with_window,
                status=CheckinStatus.APPROVED,
                special_class__date__gte=global_start,
                special_class__date__lte=reference_date,
            )
            .exclude(special_class__status=SessionStatus.CANCELLED)
            .values_list("person_id", "special_class__date")
        )
        for person_id, checkin_date in special_checkins:
            approved_dates[person_id].add(checkin_date)

    results = {}
    for pid, person in person_by_id.items():
        current = current_by_person.get(pid)
        if current is None:
            results[pid] = _empty_progress(person, reference_date, "Sem registro de graduação.")
            continue

        rule = rules_by_key.get((current.belt_rank.pk, current.grade_number))
        months_in_current_grade = _months_between(current.awarded_at, reference_date)

        if rule is None:
            results[pid] = _empty_progress(
                person,
                reference_date,
                "Sem regra de graduação cadastrada para esta faixa/grau.",
                current=current,
                months_in_current_grade=months_in_current_grade,
            )
            continue

        window_start, window_end = windows[pid]
        approved_classes = len({
            checkin_date
            for checkin_date in approved_dates.get(pid, ())
            if window_start <= checkin_date <= window_end
        })
        required_classes = rule.min_classes_required
        missing_classes = max(0, required_classes - approved_classes)
        required_months = rule.min_months_in_current_grade
        months_remaining = max(0, required_months - months_in_current_grade)

        if rule.promotes_to_next_rank:
            target_belt_rank = current.belt_rank.next_rank
            target_grade_number = 0
        else:
            target_belt_rank = current.belt_rank
            target_grade_number = rule.to_grade

        age = person.get_age(reference_date)
        age_blocker = ""
        if target_belt_rank is not None and target_belt_rank.min_age and age is not None:
            if age < target_belt_rank.min_age:
                age_blocker = (
                    f"Idade mínima da faixa {target_belt_rank.display_name}: "
                    f"{target_belt_rank.min_age} anos."
                )

        is_eligible = (
            months_remaining == 0
            and missing_classes == 0
            and target_belt_rank is not None
            and not age_blocker
        )

        progress_pct = _compute_progress_pct(
            months_in_current_grade=months_in_current_grade,
            required_months=required_months,
            approved_classes=approved_classes,
            required_classes=required_classes,
        )

        results[pid] = SimpleNamespace(
            person=person,
            current_belt_rank=current.belt_rank,
            current_grade_number=current.grade_number,
            current_graduation_date=current.awarded_at,
            applicable_rule=rule,
            target_belt_rank=target_belt_rank,
            target_grade_number=target_grade_number,
            months_in_current_grade=months_in_current_grade,
            required_months=required_months,
            months_remaining=months_remaining,
            approved_classes_in_window=approved_classes,
            required_classes=required_classes,
            missing_classes=missing_classes,
            window_start=window_start,
            window_end=window_end,
            is_eligible=is_eligible,
            progress_pct=progress_pct,
            blocker=age_blocker,
        )

    return results


def _compute_progress_pct(*, months_in_current_grade, required_months, approved_classes, required_classes):
    parts = []
    if required_months > 0:
        parts.append(min(1.0, months_in_current_grade / required_months))
    if required_classes > 0:
        parts.append(min(1.0, approved_classes / required_classes))
    if not parts:
        return 100.0
    return round(sum(parts) / len(parts) * 100.0, 1)


@transaction.atomic
def register_graduation(*, person, belt_rank, grade_number, awarded_by=None, awarded_at=None, notes=""):
    awarded_at = awarded_at or timezone.localdate()
    if grade_number > belt_rank.max_grades:
        raise ValueError("Grau acima do máximo permitido para esta faixa.")
    return Graduation.objects.create(
        person=person,
        belt_rank=belt_rank,
        grade_number=grade_number,
        awarded_at=awarded_at,
        awarded_by=awarded_by,
        notes=notes or "",
    )


@transaction.atomic
def ensure_initial_graduation_for_beginner(person, awarded_at=None):
    existing = (
        Graduation.objects.filter(person=person)
        .select_related("belt_rank")
        .order_by("-awarded_at", "-created_at")
        .first()
    )
    if existing is not None:
        return existing
    if person.jiu_jitsu_belt:
        return None

    awarded_at = awarded_at or (
        person.created_at.date() if person.created_at else timezone.localdate()
    )
    belt_rank = get_initial_belt_rank_for_person(person, awarded_at)
    if belt_rank is None:
        return None

    return Graduation.objects.create(
        person=person,
        belt_rank=belt_rank,
        grade_number=0,
        awarded_at=awarded_at,
        notes="Graduação inicial automática no cadastro.",
    )


def get_graduation_history(person, reference_date=None):
    reference_date = reference_date or timezone.localdate()
    graduations = list(
        Graduation.objects.filter(person=person)
        .select_related("belt_rank", "awarded_by")
        .order_by("awarded_at", "created_at")
    )

    tip_start, tip_width, stripe_w, stripe_gap = 232, 88, 12, 5

    entries = []
    for index, graduation in enumerate(graduations):
        next_date = (
            graduations[index + 1].awarded_at
            if index + 1 < len(graduations)
            else reference_date
        )
        period_months = _months_between(graduation.awarded_at, next_date)
        period_days = max(0, (next_date - graduation.awarded_at).days)
        is_current = index == len(graduations) - 1

        if graduation.belt_rank:
            slots = graduation.belt_rank.get_grade_slots(graduation.grade_number)
            n = len(slots)
            if n > 0:
                total_w = n * stripe_w + (n - 1) * stripe_gap
                sx = tip_start + (tip_width - total_w) // 2
                belt_stripes = [{"x": sx + i * (stripe_w + stripe_gap), "filled": f} for i, f in enumerate(slots)]
            else:
                belt_stripes = []
        else:
            belt_stripes = []

        entries.append(SimpleNamespace(
            graduation=graduation,
            belt_rank=graduation.belt_rank,
            grade_number=graduation.grade_number,
            awarded_at=graduation.awarded_at,
            awarded_by=graduation.awarded_by,
            notes=graduation.notes,
            period_months=period_months,
            period_days=period_days,
            until_date=next_date,
            is_current=is_current,
            belt_stripes=belt_stripes,
        ))

    entries.reverse()
    return entries
