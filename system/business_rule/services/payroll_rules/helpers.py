from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.conf import settings
from django.utils import timezone
from system.business_rule.services.payroll_rules.constants import CENT, PayrollRuleError, ZERO


def eligible_paid_cutoff(reference_month, as_of_date):
    _, period_end = month_bounds(reference_month)
    cutoff = as_of_date - timedelta(days=_payroll_refund_hold_days())
    return min(period_end, cutoff)


def _payroll_refund_hold_days():
    return max(int(getattr(settings, "PAYROLL_REFUND_HOLD_DAYS", 7) or 0), 0)


def payout_available_on(order):
    paid_on = local_date(order.paid_at)
    if paid_on is None:
        return None
    return paid_on + timedelta(days=_payroll_refund_hold_days())


def local_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not hasattr(value, "date"):
        return value
    return timezone.localtime(value).date()


def month_bounds(reference_month):
    first = first_of_month(reference_month)
    return first, first.replace(day=monthrange(first.year, first.month)[1])


def first_of_month(reference_date):
    return date(reference_date.year, reference_date.month, 1)


def scheduled_date(reference_month, payment_day):
    day = min(max(int(payment_day), 1), 28)
    return reference_month.replace(day=day)


def money(value):
    if value in (None, ""):
        return ZERO
    try:
        return Decimal(str(value).replace(",", ".")).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise PayrollRuleError("Valor de repasse inválido.") from exc


def percentage(value):
    percentage = money(value)
    if percentage < ZERO or percentage > Decimal("100.00"):
        raise PayrollRuleError("Percentual de repasse deve ficar entre 0 e 100.")
    return percentage
