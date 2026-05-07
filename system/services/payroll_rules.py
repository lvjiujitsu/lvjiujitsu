import json
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from system.constants import CLASS_STAFF_PERSON_TYPE_CODES
from system.models.asaas import PayoutStatus, TeacherPayrollConfig
from system.models.calendar import CheckinStatus, ClassCheckin, SpecialClassCheckin
from system.models.class_membership import ClassEnrollment, EnrollmentStatus
from system.models.registration_order import PaymentStatus, RegistrationOrder


PAYROLL_RULES_VERSION = 1
PAYROLL_METHOD_FIXED_MONTHLY = "fixed_monthly"
PAYROLL_METHOD_PER_STUDENT_FIXED = "per_student_fixed"
PAYROLL_METHOD_STUDENT_PERCENTAGE = "student_percentage"
PAYROLL_METHOD_PER_CLASS_ATTENDANCE = "per_class_attendance"
PAYROLL_SCOPE_ALL = "all"
PAYROLL_SCOPE_CLASS_GROUP = "class_group"

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


def calculate_monthly_payroll(person, *, reference_month=None):
    reference_month = _first_of_month(reference_month or timezone.localdate())
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return _empty_calculation(person, reference_month)
    if not config.is_active:
        calculation = _empty_calculation(person, reference_month)
        calculation["config"] = config
        return calculation

    rules = _get_effective_rules(config)
    person_group_ids_by_code = _get_staff_class_group_ids_by_code(person)
    entries_by_rule = []
    fixed_total = ZERO
    student_total = ZERO
    class_total = ZERO
    student_ids = set()
    class_attendance_count = 0

    for rule in rules:
        method = rule["method"]
        group_ids = _matching_group_ids(rule, person_group_ids_by_code)
        if method == PAYROLL_METHOD_FIXED_MONTHLY:
            if _rule_applies_to_person(rule, group_ids):
                fixed_total += _money(rule["amount"])
        elif method == PAYROLL_METHOD_PER_STUDENT_FIXED:
            count = _count_active_students(group_ids, reference_month)
            student_ids.update(_active_student_ids(group_ids, reference_month))
            student_total += _money(rule["amount"]) * count
        elif method == PAYROLL_METHOD_STUDENT_PERCENTAGE:
            rule_entries = _get_paid_student_entries(group_ids, reference_month)
            entries_by_rule.extend(rule_entries)
            percentage = _percentage(rule["percentage"]) / Decimal("100")
            student_total += sum(
                (_money(entry["amount"]) * percentage for entry in rule_entries),
                ZERO,
            )
            student_ids.update(entry["person"].pk for entry in rule_entries)
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
    total = _money(fixed_total + student_total + class_total)
    return {
        "person": person,
        "config": config,
        "reference_month": reference_month,
        "scheduled_for": _scheduled_date(reference_month, config.payment_day),
        "rules": rules,
        "rule_summaries": format_payroll_rules(config),
        "fixed_total": fixed_total,
        "student_total": student_total,
        "class_total": class_total,
        "total": total,
        "student_count": len(student_ids),
        "class_attendance_count": class_attendance_count,
        "entries": entries_by_rule,
    }


def format_payroll_rules(config):
    rules = _get_effective_rules(config)
    summaries = []
    for rule in rules:
        method_label = PAYROLL_METHOD_LABELS.get(rule["method"], rule["method"])
        value = _rule_value_label(rule)
        scope = rule.get("class_group_code") or "todas as turmas"
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
        f"({calculation['class_attendance_count']} presenca(s))."
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
        class_group_code = (rule.get("class_group_code") or "").strip()
        if not class_group_code:
            raise PayrollRuleError("Regra por turma exige class_group_code.")
        normalized["class_group_code"] = class_group_code
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


def _get_staff_class_group_ids_by_code(person):
    group_map = {
        group.code: group.pk
        for group in person.primary_class_groups.filter(is_active=True).only("pk", "code")
    }
    for assignment in person.class_instructor_assignments.select_related("class_group").filter(
        class_group__is_active=True,
    ):
        group_map[assignment.class_group.code] = assignment.class_group_id
    return group_map


def _matching_group_ids(rule, person_group_ids_by_code):
    if rule["scope"] == PAYROLL_SCOPE_ALL:
        return set(person_group_ids_by_code.values())
    group_id = person_group_ids_by_code.get(rule.get("class_group_code"))
    return {group_id} if group_id else set()


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


def _get_paid_student_entries(group_ids, reference_month):
    if not group_ids:
        return []
    period_start, period_end = _month_bounds(reference_month)
    orders = (
        RegistrationOrder.objects.filter(
            payment_status=PaymentStatus.PAID,
            paid_at__date__gte=period_start,
            paid_at__date__lte=period_end,
            total__gt=0,
        )
        .select_related("person", "plan")
        .order_by("paid_at", "pk")
    )
    entries = []
    for order in orders:
        linked_students = _get_order_students_for_groups(order.person, group_ids)
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
                }
            )
    return entries


def _get_order_students_for_groups(billing_person, group_ids):
    candidate_ids = {billing_person.pk}
    candidate_ids.update(
        billing_person.outgoing_relationships.values_list("target_person_id", flat=True)
    )
    enrollments = (
        ClassEnrollment.objects.filter(
            person_id__in=candidate_ids,
            class_group_id__in=group_ids,
            status=EnrollmentStatus.ACTIVE,
        )
        .select_related("person")
        .order_by("person__full_name", "person_id")
    )
    students = []
    seen = set()
    for enrollment in enrollments:
        if enrollment.person_id in seen:
            continue
        students.append(enrollment.person)
        seen.add(enrollment.person_id)
    return students


def _count_class_attendances(person, group_ids, reference_month, *, include_special):
    period_start, period_end = _month_bounds(reference_month)
    total = 0
    if group_ids:
        total += ClassCheckin.objects.filter(
            session__schedule__class_group_id__in=group_ids,
            session__date__gte=period_start,
            session__date__lte=period_end,
            status=CheckinStatus.APPROVED,
        ).count()
    if include_special:
        total += SpecialClassCheckin.objects.filter(
            special_class__teacher=person,
            special_class__date__gte=period_start,
            special_class__date__lte=period_end,
            status=CheckinStatus.APPROVED,
        ).count()
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
        "total": ZERO,
        "student_count": 0,
        "class_attendance_count": 0,
        "entries": [],
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
