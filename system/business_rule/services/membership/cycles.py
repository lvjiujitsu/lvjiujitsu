import calendar
from datetime import datetime, timezone as dt_timezone
from system.business_rule.models.plan import BillingCycle


def from_unix(value):
    if value in (None, 0):
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=dt_timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


MONTHS_BY_BILLING_CYCLE = {
    BillingCycle.MONTHLY: 1,
    BillingCycle.QUARTERLY: 3,
    BillingCycle.SEMIANNUAL: 6,
    BillingCycle.ANNUAL: 12,
}


def add_billing_cycle(start, billing_cycle):
    months = MONTHS_BY_BILLING_CYCLE.get(billing_cycle, 1)
    return add_months(start, months)


def get_billing_cycle_day_count(start, billing_cycle):
    end = add_billing_cycle(start, billing_cycle)
    return max((end - start).days, 1)


def add_months(value, months):
    month_index = value.month - 1 + months
    target_year = value.year + month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(value.day, calendar.monthrange(target_year, target_month)[1])
    return value.replace(year=target_year, month=target_month, day=target_day)
