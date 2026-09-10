from decimal import Decimal
from django.utils import timezone
from system.business_rule.models.registration_order import PaymentStatus, RegistrationOrder
from system.business_rule.services.payroll_rules.constants import PAYROLL_METHOD_PER_STUDENT_FIXED, PAYROLL_METHOD_STUDENT_PERCENTAGE, PAYROLL_REFUND_ABSORPTION_PREFIX, PAYROLL_REFUND_NOTE_PREFIX, PAYROLL_RULES_VERSION, PayrollRuleError, ZERO
from system.business_rule.services.payroll_rules.helpers import local_date, money, month_bounds, percentage
from system.business_rule.services.payroll_rules.notes import append_order_note_record, read_order_note_records
from system.business_rule.services.payroll_rules.students import get_order_students_for_groups


def append_order_refund_record(
    order,
    amount,
    *,
    source="",
    cumulative=False,
    reason="",
    save=True,
):
    refund_amount = money(amount)
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
    return append_order_note_record(
        order,
        PAYROLL_REFUND_NOTE_PREFIX,
        payload,
        save=save,
    )


def record_refund_absorptions(calculation, *, source="monthly_payroll"):
    remaining = min(
        money(calculation.get("refund_adjustment_total")),
        money(calculation.get("gross_total")),
    )
    if remaining <= ZERO:
        return []

    records = []
    reference_month = calculation["reference_month"]
    person = calculation["person"]
    for entry in calculation.get("refund_entries", []):
        if remaining <= ZERO:
            break
        amount = min(money(entry["amount"]), remaining)
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


def get_refund_entries_for_rule(rule, group_ids, reference_month, person):
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
        linked_students = get_order_students_for_groups(
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
    _, period_end = month_bounds(reference_month)
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
        percentage = percentage(rule["percentage"]) / Decimal("100")
        order_amount = money(order.net_amount if order.net_amount else order.total)
        allocated = money(order_amount / Decimal(len(linked_students)))
        adjustment = money(allocated * percentage * ratio)
    elif rule["method"] == PAYROLL_METHOD_PER_STUDENT_FIXED:
        adjustment = money(money(rule["amount"]) * ratio)
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


def _refund_should_adjust_period(order, reference_month):
    period_start, _ = month_bounds(reference_month)
    paid_on = local_date(order.paid_at)
    refunded_on = local_date(order.refunded_at)
    if paid_on is None or refunded_on is None:
        return False
    if paid_on >= period_start and order.payment_status == PaymentStatus.REFUNDED:
        return False
    return True


def _refund_ratio(order, refund_amount):
    total = money(order.total)
    if total <= ZERO:
        return ZERO
    return min(money(refund_amount), total) / total


def apply_recorded_absorptions(entries, person):
    if not entries:
        return []
    adjusted = []
    absorbed_by_order = {}
    for entry in entries:
        order = entry["order"]
        if order.pk not in absorbed_by_order:
            absorbed_by_order[order.pk] = _get_recorded_absorption_amount(order, person)
        remaining_absorbed = absorbed_by_order[order.pk]
        amount = money(entry["amount"])
        if remaining_absorbed >= amount:
            absorbed_by_order[order.pk] = remaining_absorbed - amount
            continue
        if remaining_absorbed > ZERO:
            amount -= remaining_absorbed
            absorbed_by_order[order.pk] = ZERO
        adjusted_entry = dict(entry)
        adjusted_entry["amount"] = money(amount)
        adjusted.append(adjusted_entry)
    return adjusted


def _get_recorded_refund_amount(order):
    records = read_order_note_records(order.notes, PAYROLL_REFUND_NOTE_PREFIX)
    incremental_total = ZERO
    cumulative_total = ZERO
    for record in records:
        amount = money(record.get("amount"))
        if record.get("cumulative"):
            cumulative_total = max(cumulative_total, amount)
        else:
            incremental_total += amount
    recorded_total = money(max(incremental_total, cumulative_total))
    if recorded_total > ZERO:
        return recorded_total
    if order.refunded_at and order.payment_status == PaymentStatus.REFUNDED:
        return money(order.total)
    return ZERO


def _get_recorded_absorption_amount(order, person):
    records = read_order_note_records(order.notes, PAYROLL_REFUND_ABSORPTION_PREFIX)
    return money(
        sum(
            (
                money(record.get("amount"))
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
    absorbed_amount = money(amount)
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
    return append_order_note_record(
        order,
        PAYROLL_REFUND_ABSORPTION_PREFIX,
        payload,
        save=True,
    )
