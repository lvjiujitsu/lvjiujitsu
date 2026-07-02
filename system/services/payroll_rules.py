import json
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.constants import CLASS_STAFF_PERSON_TYPE_CODES
from system.models.asaas import TeacherPayrollConfig
from system.models.calendar import (
    CheckinStatus,
    ClassCheckin,
    SessionStatus,
    SpecialClassCheckin,
)
from system.models.class_membership import ClassEnrollment, EnrollmentStatus
from system.models.registration_order import PaymentStatus, RegistrationOrder


PAYROLL_RULES_VERSION = 1
PAYROLL_METHOD_FIXED_MONTHLY = "fixed_monthly"
PAYROLL_METHOD_PER_STUDENT_FIXED = "per_student_fixed"
PAYROLL_METHOD_STUDENT_PERCENTAGE = "student_percentage"
PAYROLL_METHOD_PER_CLASS_ATTENDANCE = "per_class_attendance"
PAYROLL_SCOPE_ALL = "all"
PAYROLL_SCOPE_CLASS_GROUP = "class_group"
PAYROLL_REFUND_NOTE_PREFIX = "PAYROLL_REFUND_ADJUSTMENT:"
PAYROLL_REFUND_ABSORPTION_PREFIX = "PAYROLL_REFUND_ABSORPTION:"

ZERO = Decimal("0.00")
CENT = Decimal("0.01")

PAYROLL_METHOD_LABELS = {
    PAYROLL_METHOD_FIXED_MONTHLY: "Fixo mensal",
    PAYROLL_METHOD_PER_STUDENT_FIXED: "Valor por aluno",
    PAYROLL_METHOD_STUDENT_PERCENTAGE: "Percentual por aluno",
    PAYROLL_METHOD_PER_CLASS_ATTENDANCE: "Valor por aluno/aula",
}


class PayrollRuleError(ValueError):
    pass


def encode_payroll_rules(rules):
    payload = {
        "version": PAYROLL_RULES_VERSION,
        "rules": [_normalize_rule(rule) for rule in rules],
    }
    return json.dumps(payload, sort_keys=True)


def decode_payroll_rules(raw_notes, *, strict=False):
    if not raw_notes:
        return {"version": PAYROLL_RULES_VERSION, "rules": []}
    try:
        payload = json.loads(raw_notes)
    except json.JSONDecodeError as exc:
        if strict:
            raise PayrollRuleError("JSON de repasse inválido.") from exc
        return {"version": PAYROLL_RULES_VERSION, "rules": [], "legacy_notes": raw_notes}
    if not isinstance(payload, dict) or "rules" not in payload:
        if strict:
            raise PayrollRuleError("Informe um objeto JSON com a chave rules.")
        return {"version": PAYROLL_RULES_VERSION, "rules": [], "legacy_notes": raw_notes}
    rules = payload.get("rules")
    if not isinstance(rules, list):
        if strict:
            raise PayrollRuleError("A chave rules deve ser uma lista.")
        rules = []
    return {
        "version": int(payload.get("version") or PAYROLL_RULES_VERSION),
        "rules": [_normalize_rule(rule) for rule in rules],
    }


def build_payroll_payload_from_form(cleaned_data):
    raw_rules = (cleaned_data.get("payroll_rules_json") or "").strip()
    if raw_rules:
        return decode_payroll_rules(raw_rules, strict=True)

    rules = []
    fixed = _money(cleaned_data.get("payroll_fixed_monthly"))
    per_student = _money(cleaned_data.get("payroll_per_student_amount"))
    percentage = _percentage(cleaned_data.get("payroll_student_percentage"))
    per_class = _money(cleaned_data.get("payroll_per_class_amount"))

    if fixed > ZERO:
        rules.append({"method": PAYROLL_METHOD_FIXED_MONTHLY, "amount": str(fixed)})
    if per_student > ZERO:
        rules.append({"method": PAYROLL_METHOD_PER_STUDENT_FIXED, "amount": str(per_student)})
    if percentage > ZERO:
        rules.append(
            {"method": PAYROLL_METHOD_STUDENT_PERCENTAGE, "percentage": str(percentage)}
        )
    if per_class > ZERO:
        rules.append(
            {"method": PAYROLL_METHOD_PER_CLASS_ATTENDANCE, "amount": str(per_class)}
        )
    return {"version": PAYROLL_RULES_VERSION, "rules": rules}


@transaction.atomic
def save_person_payroll_config(person, cleaned_data):
    enabled = bool(cleaned_data.get("payroll_enabled"))
    is_staff = person.has_type_code(*CLASS_STAFF_PERSON_TYPE_CODES)
    existing = _get_existing_config(person)

    if not is_staff:
        if existing is not None and existing.is_active:
            existing.is_active = False
            existing.save(update_fields=["is_active", "updated_at"])
        if enabled:
            raise PayrollRuleError("Repasse permitido apenas para Professor ou Administrativo.")
        return existing

    if not enabled:
        if existing is not None and existing.is_active:
            existing.is_active = False
            existing.save(update_fields=["is_active", "updated_at"])
        return existing

    payload = build_payroll_payload_from_form(cleaned_data)
    monthly_salary = _money(cleaned_data.get("payroll_fixed_monthly"))
    if monthly_salary == ZERO:
        monthly_salary = _first_fixed_monthly_amount(payload["rules"])
    payment_day = int(cleaned_data.get("payroll_payment_day") or 28)
    payment_day = min(max(payment_day, 1), 28)

    config, _ = TeacherPayrollConfig.objects.update_or_create(
        person=person,
        defaults={
            "monthly_salary": monthly_salary,
            "payment_day": payment_day,
            "is_active": True,
            "notes": encode_payroll_rules(payload["rules"]),
        },
    )
    return config


def append_order_refund_record(
    order,
    amount,
    *,
    source="",
    cumulative=False,
    reason="",
    save=True,
):
    refund_amount = _money(amount)
    if refund_amount <= ZERO:
        raise PayrollRuleError("Valor de estorno deve ser maior que zero.")
    payload = {
        "version": PAYROLL_RULES_VERSION,
        "amount": str(refund_amount),
        "source": source or "manual",
        "cumulative": bool(cumulative),
        "reason": reason or "",
        "recorded_at": timezone.now().isoformat(),
    }
    return _append_order_note_record(
        order,
        PAYROLL_REFUND_NOTE_PREFIX,
        payload,
        save=save,
    )


def record_refund_absorptions(calculation, *, source="monthly_payroll"):
    remaining = min(
        _money(calculation.get("refund_adjustment_total")),
        _money(calculation.get("gross_total")),
    )
    if remaining <= ZERO:
        return []

    records = []
    reference_month = calculation["reference_month"]
    person = calculation["person"]
    for entry in calculation.get("refund_entries", []):
        if remaining <= ZERO:
            break
        amount = min(_money(entry["amount"]), remaining)
        _append_order_refund_absorption(
            entry["order"],
            person,
            amount,
            reference_month=reference_month,
            source=source,
        )
        records.append({"order": entry["order"], "amount": amount})
        remaining -= amount
    return records


def _get_existing_config(person):
    try:
        return person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return None


def get_payroll_form_initial(person):
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return {
            "payroll_enabled": False,
            "payroll_payment_day": 28,
            "payroll_fixed_monthly": ZERO,
            "payroll_per_student_amount": ZERO,
            "payroll_student_percentage": ZERO,
            "payroll_per_class_amount": ZERO,
            "payroll_rules_json": "",
        }

    payload = decode_payroll_rules(config.notes)
    initial = {
        "payroll_enabled": config.is_active,
        "payroll_payment_day": config.payment_day,
        "payroll_fixed_monthly": config.monthly_salary,
        "payroll_per_student_amount": ZERO,
        "payroll_student_percentage": ZERO,
        "payroll_per_class_amount": ZERO,
        "payroll_rules_json": config.notes if payload["rules"] else "",
    }
    for rule in payload["rules"]:
        if rule["scope"] != PAYROLL_SCOPE_ALL:
            continue
        if rule["method"] == PAYROLL_METHOD_PER_STUDENT_FIXED:
            initial["payroll_per_student_amount"] = _money(rule["amount"])
        elif rule["method"] == PAYROLL_METHOD_STUDENT_PERCENTAGE:
            initial["payroll_student_percentage"] = _percentage(rule["percentage"])
        elif rule["method"] == PAYROLL_METHOD_PER_CLASS_ATTENDANCE:
            initial["payroll_per_class_amount"] = _money(rule["amount"])
    return initial


def calculate_monthly_payroll(person, *, reference_month=None, as_of_date=None):
    reference_month = _first_of_month(reference_month or timezone.localdate())
    as_of_date = as_of_date or timezone.localdate()
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return _empty_calculation(person, reference_month)
    if not config.is_active:
        calculation = _empty_calculation(person, reference_month)
        calculation["config"] = config
        return calculation

    rules = _get_effective_rules(config)
    person_group_ids = _get_staff_class_group_ids(person)
    entries_by_rule = []
    held_entries = []
    refund_entries = []
    fixed_total = ZERO
    student_total = ZERO
    class_total = ZERO
    student_ids = set()
    class_attendance_count = 0

    for rule in rules:
        method = rule["method"]
        group_ids = _matching_group_ids(rule, person_group_ids)
        if method == PAYROLL_METHOD_FIXED_MONTHLY:
            if _rule_applies_to_person(rule, group_ids):
                fixed_total += _money(rule["amount"])
        elif method == PAYROLL_METHOD_PER_STUDENT_FIXED:
            rule_entries = _get_paid_student_entries(
                group_ids,
                reference_month,
                as_of_date=as_of_date,
            )
            held_entries.extend(
                _get_held_student_entries(
                    group_ids,
                    reference_month,
                    as_of_date=as_of_date,
                )
            )
            entry_student_ids = {entry["person"].pk for entry in rule_entries}
            count = len(entry_student_ids)
            student_ids.update(entry_student_ids)
            student_total += _money(rule["amount"]) * count
            refund_entries.extend(
                _get_refund_entries_for_rule(
                    rule,
                    group_ids,
                    reference_month,
                    person,
                )
            )
        elif method == PAYROLL_METHOD_STUDENT_PERCENTAGE:
            rule_entries = _get_paid_student_entries(
                group_ids,
                reference_month,
                as_of_date=as_of_date,
            )
            entries_by_rule.extend(rule_entries)
            held_entries.extend(
                _get_held_student_entries(
                    group_ids,
                    reference_month,
                    as_of_date=as_of_date,
                )
            )
            percentage = _percentage(rule["percentage"]) / Decimal("100")
            student_total += sum(
                (_money(entry["amount"]) * percentage for entry in rule_entries),
                ZERO,
            )
            student_ids.update(entry["person"].pk for entry in rule_entries)
            refund_entries.extend(
                _get_refund_entries_for_rule(
                    rule,
                    group_ids,
                    reference_month,
                    person,
                )
            )
        elif method == PAYROLL_METHOD_PER_CLASS_ATTENDANCE:
            count = _count_class_attendances(
                person,
                group_ids,
                reference_month,
                include_special=rule["scope"] == PAYROLL_SCOPE_ALL,
            )
            class_attendance_count += count
            class_total += _money(rule["amount"]) * count

    fixed_total = _money(fixed_total)
    student_total = _money(student_total)
    class_total = _money(class_total)
    gross_total = _money(fixed_total + student_total + class_total)
    refund_entries = _apply_recorded_absorptions(refund_entries, person)
    refund_adjustment_total = _money(
        sum((_money(entry["amount"]) for entry in refund_entries), ZERO)
    )
    held_total = _money(
        sum((_money(entry["amount"]) for entry in held_entries), ZERO)
    )
    total_before_floor = _money(gross_total - refund_adjustment_total)
    carryover_adjustment = _money(abs(min(total_before_floor, ZERO)))
    total = _money(max(total_before_floor, ZERO))
    return {
        "person": person,
        "config": config,
        "reference_month": reference_month,
        "as_of_date": as_of_date,
        "scheduled_for": _scheduled_date(reference_month, config.payment_day),
        "rules": rules,
        "rule_summaries": format_payroll_rules(config),
        "fixed_total": fixed_total,
        "student_total": student_total,
        "class_total": class_total,
        "gross_total": gross_total,
        "held_total": held_total,
        "refund_adjustment_total": refund_adjustment_total,
        "carryover_adjustment": carryover_adjustment,
        "total": total,
        "student_count": len(student_ids),
        "class_attendance_count": class_attendance_count,
        "entries": entries_by_rule,
        "held_entries": held_entries,
        "refund_entries": refund_entries,
    }


def format_payroll_rules(config):
    rules = _get_effective_rules(config)
    summaries = []
    for rule in rules:
        method_label = PAYROLL_METHOD_LABELS.get(rule["method"], rule["method"])
        value = _rule_value_label(rule)
        scope = rule.get("class_group_id") or "todas as turmas"
        summaries.append(
            {
                "method": rule["method"],
                "method_label": method_label,
                "value": value,
                "scope": scope,
            }
        )
    if not summaries and config.monthly_salary == ZERO:
        summaries.append(
            {
                "method": PAYROLL_METHOD_FIXED_MONTHLY,
                "method_label": "Sem repasse",
                "value": "R$ 0,00",
                "scope": "todas as turmas",
            }
        )
    return summaries


def render_payroll_summary(calculation):
    return (
        f"Fechamento {calculation['reference_month'].strftime('%m/%Y')}: "
        f"fixo R$ {calculation['fixed_total']}, "
        f"alunos R$ {calculation['student_total']} "
        f"({calculation['student_count']} aluno(s)), "
        f"aulas R$ {calculation['class_total']} "
        f"({calculation['class_attendance_count']} presenca(s)), "
        f"retido R$ {calculation['held_total']}, "
        f"abatimentos R$ {calculation['refund_adjustment_total']}, "
        f"total R$ {calculation['total']}."
    )


def get_staff_financial_context(person, *, reference_month=None):
    calculation = calculate_monthly_payroll(person, reference_month=reference_month)
    recent_payouts = list(
        person.teacher_payouts.select_related("bank_account").order_by(
            "-reference_month",
            "-created_at",
        )[:10]
    )
    return {
        "calculation": calculation,
        "recent_payouts": recent_payouts,
        "linked_entries": calculation["entries"],
        "held_entries": calculation["held_entries"],
        "refund_entries": calculation["refund_entries"],
    }


def _normalize_rule(rule):
    if not isinstance(rule, dict):
        raise PayrollRuleError("Regra de repasse deve ser um objeto.")
    method = rule.get("method")
    if method not in PAYROLL_METHOD_LABELS:
        raise PayrollRuleError(f"Método de repasse inválido: {method}")
    normalized = {
        "method": method,
        "scope": rule.get("scope") or PAYROLL_SCOPE_ALL,
    }
    if normalized["scope"] not in (PAYROLL_SCOPE_ALL, PAYROLL_SCOPE_CLASS_GROUP):
        raise PayrollRuleError("Escopo de repasse inválido.")
    if normalized["scope"] == PAYROLL_SCOPE_CLASS_GROUP:
        class_group_id = rule.get("class_group_id")
        if not class_group_id:
            raise PayrollRuleError("Regra por turma exige class_group_id.")
        try:
            normalized["class_group_id"] = int(class_group_id)
        except (TypeError, ValueError):
            raise PayrollRuleError("class_group_id deve ser um número inteiro.")
    if method in (
        PAYROLL_METHOD_FIXED_MONTHLY,
        PAYROLL_METHOD_PER_STUDENT_FIXED,
        PAYROLL_METHOD_PER_CLASS_ATTENDANCE,
    ):
        normalized["amount"] = str(_money(rule.get("amount")))
    if method == PAYROLL_METHOD_STUDENT_PERCENTAGE:
        normalized["percentage"] = str(_percentage(rule.get("percentage")))
    return normalized


def _get_effective_rules(config):
    payload = decode_payroll_rules(config.notes)
    rules = payload["rules"]
    if rules:
        return rules
    if config.monthly_salary != ZERO:
        return [
            {
                "method": PAYROLL_METHOD_FIXED_MONTHLY,
                "scope": PAYROLL_SCOPE_ALL,
                "amount": str(_money(config.monthly_salary)),
            }
        ]
    return []


def _get_staff_class_group_ids(person):
    primary_ids = set(
        person.primary_class_groups.filter(is_active=True).values_list("pk", flat=True)
    )
    assignment_ids = set(
        person.class_instructor_assignments
        .filter(class_group__is_active=True)
        .values_list("class_group_id", flat=True)
    )
    return primary_ids | assignment_ids


def _matching_group_ids(rule, person_group_ids):
    if rule["scope"] == PAYROLL_SCOPE_ALL:
        return person_group_ids
    group_id = rule.get("class_group_id")
    if group_id and int(group_id) in person_group_ids:
        return {int(group_id)}
    return set()


def _rule_applies_to_person(rule, group_ids):
    return rule["scope"] == PAYROLL_SCOPE_ALL or bool(group_ids)


def _count_active_students(group_ids, reference_month):
    return len(_active_student_ids(group_ids, reference_month))


def _active_student_ids(group_ids, reference_month):
    if not group_ids:
        return set()
    _, period_end = _month_bounds(reference_month)
    return set(
        ClassEnrollment.objects.filter(
            class_group_id__in=group_ids,
            status=EnrollmentStatus.ACTIVE,
            created_at__date__lte=period_end,
        ).values_list("person_id", flat=True)
    )


def _get_paid_student_entries(group_ids, reference_month, *, as_of_date):
    cutoff = _eligible_paid_cutoff(reference_month, as_of_date)
    period_start, _ = _month_bounds(reference_month)
    if not group_ids or cutoff < period_start:
        return []
    orders = _get_student_entry_orders(
        period_start=period_start,
        period_end=cutoff,
    )
    return _build_student_entries_from_orders(orders, group_ids, active_only=True)


def _get_held_student_entries(group_ids, reference_month, *, as_of_date):
    if not group_ids:
        return []
    period_start, period_end = _month_bounds(reference_month)
    cutoff = _eligible_paid_cutoff(reference_month, as_of_date)
    start = period_start
    if cutoff >= period_start:
        start = cutoff + timedelta(days=1)
    end = min(period_end, as_of_date)
    if end < start:
        return []
    orders = _get_student_entry_orders(period_start=start, period_end=end)
    return _build_student_entries_from_orders(orders, group_ids, active_only=True)


def _get_student_entry_orders(*, period_start, period_end):
    return (
        RegistrationOrder.objects.filter(
            payment_status=PaymentStatus.PAID,
            paid_at__date__gte=period_start,
            paid_at__date__lte=period_end,
            total__gt=0,
        )
        .select_related("person", "plan")
        .order_by("paid_at", "pk")
    )


def _build_student_entries_from_orders(orders, group_ids, *, active_only):
    entries = []
    for order in orders:
        linked_students = _get_order_students_for_groups(
            order.person,
            group_ids,
            active_only=active_only,
        )
        if not linked_students:
            continue
        order_amount = _money(order.net_amount if order.net_amount else order.total)
        allocated = _money(order_amount / Decimal(len(linked_students)))
        for student in linked_students:
            entries.append(
                {
                    "person": student,
                    "order": order,
                    "amount": allocated,
                    "expected_deposit_date": order.expected_deposit_date,
                    "paid_at": order.paid_at,
                    "payout_available_on": _payout_available_on(order),
                }
            )
    return entries


def _get_refund_entries_for_rule(rule, group_ids, reference_month, person):
    if not group_ids:
        return []
    orders = _get_refunded_orders(reference_month)
    entries = []
    for order in orders:
        if not _refund_should_adjust_period(order, reference_month):
            continue
        refund_amount = _get_recorded_refund_amount(order)
        if refund_amount <= ZERO:
            continue
        linked_students = _get_order_students_for_groups(
            order.person,
            group_ids,
            active_only=False,
        )
        if not linked_students:
            continue
        ratio = _refund_ratio(order, refund_amount)
        if ratio <= ZERO:
            continue
        entries.extend(
            _build_refund_entries_for_order(
                rule,
                order,
                linked_students,
                ratio,
            )
        )
    return entries


def _get_refunded_orders(reference_month):
    _, period_end = _month_bounds(reference_month)
    return (
        RegistrationOrder.objects.filter(
            refunded_at__isnull=False,
            refunded_at__date__lte=period_end,
            paid_at__isnull=False,
            total__gt=0,
        )
        .select_related("person", "plan")
        .order_by("refunded_at", "pk")
    )


def _build_refund_entries_for_order(rule, order, linked_students, ratio):
    entries = []
    if rule["method"] == PAYROLL_METHOD_STUDENT_PERCENTAGE:
        percentage = _percentage(rule["percentage"]) / Decimal("100")
        order_amount = _money(order.net_amount if order.net_amount else order.total)
        allocated = _money(order_amount / Decimal(len(linked_students)))
        adjustment = _money(allocated * percentage * ratio)
    elif rule["method"] == PAYROLL_METHOD_PER_STUDENT_FIXED:
        adjustment = _money(_money(rule["amount"]) * ratio)
    else:
        return entries
    if adjustment <= ZERO:
        return entries
    refunded_amount = _get_recorded_refund_amount(order)
    for student in linked_students:
        entries.append(
            {
                "person": student,
                "order": order,
                "amount": adjustment,
                "refunded_amount": refunded_amount,
                "refunded_at": order.refunded_at,
            }
        )
    return entries


def _get_order_students_for_groups(billing_person, group_ids, *, active_only=True):
    candidate_ids = {billing_person.pk}
    candidate_ids.update(
        billing_person.outgoing_relationships.values_list("target_person_id", flat=True)
    )
    enrollments = ClassEnrollment.objects.filter(
        person_id__in=candidate_ids,
        class_group_id__in=group_ids,
    )
    if active_only:
        enrollments = enrollments.filter(status=EnrollmentStatus.ACTIVE)
    enrollments = enrollments.select_related("person").order_by(
        "person__full_name",
        "person_id",
    )
    students = []
    seen = set()
    for enrollment in enrollments:
        if enrollment.person_id in seen:
            continue
        students.append(enrollment.person)
        seen.add(enrollment.person_id)
    return students


def _eligible_paid_cutoff(reference_month, as_of_date):
    _, period_end = _month_bounds(reference_month)
    cutoff = as_of_date - timedelta(days=_payroll_refund_hold_days())
    return min(period_end, cutoff)


def _payroll_refund_hold_days():
    return max(int(getattr(settings, "PAYROLL_REFUND_HOLD_DAYS", 7) or 0), 0)


def _payout_available_on(order):
    paid_on = _local_date(order.paid_at)
    if paid_on is None:
        return None
    return paid_on + timedelta(days=_payroll_refund_hold_days())


def _refund_should_adjust_period(order, reference_month):
    period_start, _ = _month_bounds(reference_month)
    paid_on = _local_date(order.paid_at)
    refunded_on = _local_date(order.refunded_at)
    if paid_on is None or refunded_on is None:
        return False
    if paid_on >= period_start and order.payment_status == PaymentStatus.REFUNDED:
        return False
    return True


def _refund_ratio(order, refund_amount):
    total = _money(order.total)
    if total <= ZERO:
        return ZERO
    return min(_money(refund_amount), total) / total


def _apply_recorded_absorptions(entries, person):
    if not entries:
        return []
    adjusted = []
    absorbed_by_order = {}
    for entry in entries:
        order = entry["order"]
        if order.pk not in absorbed_by_order:
            absorbed_by_order[order.pk] = _get_recorded_absorption_amount(order, person)
        remaining_absorbed = absorbed_by_order[order.pk]
        amount = _money(entry["amount"])
        if remaining_absorbed >= amount:
            absorbed_by_order[order.pk] = remaining_absorbed - amount
            continue
        if remaining_absorbed > ZERO:
            amount -= remaining_absorbed
            absorbed_by_order[order.pk] = ZERO
        adjusted_entry = dict(entry)
        adjusted_entry["amount"] = _money(amount)
        adjusted.append(adjusted_entry)
    return adjusted


def _get_recorded_refund_amount(order):
    records = _read_order_note_records(order.notes, PAYROLL_REFUND_NOTE_PREFIX)
    incremental_total = ZERO
    cumulative_total = ZERO
    for record in records:
        amount = _money(record.get("amount"))
        if record.get("cumulative"):
            cumulative_total = max(cumulative_total, amount)
        else:
            incremental_total += amount
    recorded_total = _money(max(incremental_total, cumulative_total))
    if recorded_total > ZERO:
        return recorded_total
    if order.refunded_at and order.payment_status == PaymentStatus.REFUNDED:
        return _money(order.total)
    return ZERO


def _get_recorded_absorption_amount(order, person):
    records = _read_order_note_records(order.notes, PAYROLL_REFUND_ABSORPTION_PREFIX)
    return _money(
        sum(
            (
                _money(record.get("amount"))
                for record in records
                if int(record.get("person_id") or 0) == person.pk
            ),
            ZERO,
        )
    )


def _append_order_refund_absorption(
    order,
    person,
    amount,
    *,
    reference_month,
    source,
):
    absorbed_amount = _money(amount)
    if absorbed_amount <= ZERO:
        return order
    payload = {
        "version": PAYROLL_RULES_VERSION,
        "amount": str(absorbed_amount),
        "person_id": person.pk,
        "reference_month": reference_month.isoformat(),
        "source": source or "monthly_payroll",
        "recorded_at": timezone.now().isoformat(),
    }
    return _append_order_note_record(
        order,
        PAYROLL_REFUND_ABSORPTION_PREFIX,
        payload,
        save=True,
    )


def _append_order_note_record(order, prefix, payload, *, save):
    line = prefix + json.dumps(payload, sort_keys=True)
    current_notes = (order.notes or "").strip()
    order.notes = "\n".join([item for item in (current_notes, line) if item])
    if save:
        order.save(update_fields=["notes", "updated_at"])
    return order


def _read_order_note_records(notes, prefix):
    records = []
    for line in (notes or "").splitlines():
        if not line.startswith(prefix):
            continue
        raw_payload = line[len(prefix):]
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise PayrollRuleError("Registro de estorno inválido.") from exc
        if not isinstance(payload, dict):
            raise PayrollRuleError("Registro de estorno deve ser um objeto.")
        records.append(payload)
    return records


def _local_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not hasattr(value, "date"):
        return value
    return timezone.localtime(value).date()


def _count_class_attendances(person, group_ids, reference_month, *, include_special):
    period_start, period_end = _month_bounds(reference_month)
    total = 0
    if group_ids:
        total += (
            ClassCheckin.objects.filter(
                session__schedule__class_group_id__in=group_ids,
                session__date__gte=period_start,
                session__date__lte=period_end,
                status=CheckinStatus.APPROVED,
            )
            .exclude(session__status=SessionStatus.CANCELLED)
            .count()
        )
    if include_special:
        total += (
            SpecialClassCheckin.objects.filter(
                special_class__teacher=person,
                special_class__date__gte=period_start,
                special_class__date__lte=period_end,
                status=CheckinStatus.APPROVED,
            )
            .exclude(special_class__status=SessionStatus.CANCELLED)
            .count()
        )
    return total


def _empty_calculation(person, reference_month):
    return {
        "person": person,
        "config": None,
        "reference_month": reference_month,
        "scheduled_for": None,
        "rules": [],
        "rule_summaries": [],
        "fixed_total": ZERO,
        "student_total": ZERO,
        "class_total": ZERO,
        "gross_total": ZERO,
        "held_total": ZERO,
        "refund_adjustment_total": ZERO,
        "carryover_adjustment": ZERO,
        "total": ZERO,
        "student_count": 0,
        "class_attendance_count": 0,
        "entries": [],
        "held_entries": [],
        "refund_entries": [],
    }


def _first_fixed_monthly_amount(rules):
    for rule in rules:
        if rule["method"] == PAYROLL_METHOD_FIXED_MONTHLY:
            return _money(rule.get("amount"))
    return ZERO


def _rule_value_label(rule):
    if rule["method"] == PAYROLL_METHOD_STUDENT_PERCENTAGE:
        return f"{_percentage(rule['percentage'])}%"
    return f"R$ {_money(rule.get('amount'))}"


def _month_bounds(reference_month):
    first = _first_of_month(reference_month)
    return first, first.replace(day=monthrange(first.year, first.month)[1])


def _first_of_month(reference_date):
    return date(reference_date.year, reference_date.month, 1)


def _scheduled_date(reference_month, payment_day):
    day = min(max(int(payment_day), 1), 28)
    return reference_month.replace(day=day)


def _money(value):
    if value in (None, ""):
        return ZERO
    try:
        return Decimal(str(value).replace(",", ".")).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise PayrollRuleError("Valor de repasse inválido.") from exc


def _percentage(value):
    percentage = _money(value)
    if percentage < ZERO or percentage > Decimal("100.00"):
        raise PayrollRuleError("Percentual de repasse deve ficar entre 0 e 100.")
    return percentage
