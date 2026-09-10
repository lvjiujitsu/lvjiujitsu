from decimal import Decimal
from django.utils import timezone
from system.business_rule.models.asaas import TeacherPayrollConfig
from system.business_rule.services.payroll_rules.constants import PAYROLL_METHOD_FIXED_MONTHLY, PAYROLL_METHOD_PER_CLASS_ATTENDANCE, PAYROLL_METHOD_PER_STUDENT_FIXED, PAYROLL_METHOD_STUDENT_PERCENTAGE, PAYROLL_SCOPE_ALL, ZERO
from system.business_rule.services.payroll_rules.helpers import first_of_month, money, percentage, scheduled_date
from system.business_rule.services.payroll_rules.refunds import apply_recorded_absorptions, get_refund_entries_for_rule
from system.business_rule.services.payroll_rules.rules import get_effective_rules, format_payroll_rules
from system.business_rule.services.payroll_rules.students import count_class_attendances, get_held_student_entries, get_paid_student_entries, get_staff_class_group_ids, matching_group_ids, rule_applies_to_person


def calculate_monthly_payroll(person, *, reference_month=None, as_of_date=None):
    reference_month = first_of_month(reference_month or timezone.localdate())
    as_of_date = as_of_date or timezone.localdate()
    try:
        config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        return _empty_calculation(person, reference_month)
    if not config.is_active:
        calculation = _empty_calculation(person, reference_month)
        calculation["config"] = config
        return calculation

    rules = get_effective_rules(config)
    person_group_ids = get_staff_class_group_ids(person)
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
        group_ids = matching_group_ids(rule, person_group_ids)
        if method == PAYROLL_METHOD_FIXED_MONTHLY:
            if rule_applies_to_person(rule, group_ids):
                fixed_total += money(rule["amount"])
        elif method == PAYROLL_METHOD_PER_STUDENT_FIXED:
            rule_entries = get_paid_student_entries(
                group_ids,
                reference_month,
                as_of_date=as_of_date,
            )
            held_entries.extend(
                get_held_student_entries(
                    group_ids,
                    reference_month,
                    as_of_date=as_of_date,
                )
            )
            entry_student_ids = {entry["person"].pk for entry in rule_entries}
            count = len(entry_student_ids)
            student_ids.update(entry_student_ids)
            student_total += money(rule["amount"]) * count
            refund_entries.extend(
                get_refund_entries_for_rule(
                    rule,
                    group_ids,
                    reference_month,
                    person,
                )
            )
        elif method == PAYROLL_METHOD_STUDENT_PERCENTAGE:
            rule_entries = get_paid_student_entries(
                group_ids,
                reference_month,
                as_of_date=as_of_date,
            )
            entries_by_rule.extend(rule_entries)
            held_entries.extend(
                get_held_student_entries(
                    group_ids,
                    reference_month,
                    as_of_date=as_of_date,
                )
            )
            percentage = percentage(rule["percentage"]) / Decimal("100")
            student_total += sum(
                (money(entry["amount"]) * percentage for entry in rule_entries),
                ZERO,
            )
            student_ids.update(entry["person"].pk for entry in rule_entries)
            refund_entries.extend(
                get_refund_entries_for_rule(
                    rule,
                    group_ids,
                    reference_month,
                    person,
                )
            )
        elif method == PAYROLL_METHOD_PER_CLASS_ATTENDANCE:
            count = count_class_attendances(
                person,
                group_ids,
                reference_month,
                include_special=rule["scope"] == PAYROLL_SCOPE_ALL,
            )
            class_attendance_count += count
            class_total += money(rule["amount"]) * count

    fixed_total = money(fixed_total)
    student_total = money(student_total)
    class_total = money(class_total)
    gross_total = money(fixed_total + student_total + class_total)
    refund_entries = apply_recorded_absorptions(refund_entries, person)
    refund_adjustment_total = money(
        sum((money(entry["amount"]) for entry in refund_entries), ZERO)
    )
    held_total = money(
        sum((money(entry["amount"]) for entry in held_entries), ZERO)
    )
    total_before_floor = money(gross_total - refund_adjustment_total)
    carryover_adjustment = money(abs(min(total_before_floor, ZERO)))
    total = money(max(total_before_floor, ZERO))
    return {
        "person": person,
        "config": config,
        "reference_month": reference_month,
        "as_of_date": as_of_date,
        "scheduled_for": scheduled_date(reference_month, config.payment_day),
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
