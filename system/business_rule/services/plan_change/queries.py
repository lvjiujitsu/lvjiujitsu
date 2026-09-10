from decimal import Decimal
from system.business_rule.models.plan import PlanPrice
from system.business_rule.models.registration_order import PaymentStatus, RegistrationOrder
from system.business_rule.services.plan_change.primitives import quantize


def get_last_paid_order(membership):
    queryset = RegistrationOrder.objects.filter(
        person=membership.person,
        payment_status__in=(PaymentStatus.PAID, PaymentStatus.EXEMPTED),
        total__gt=Decimal("0"),
    ).filter(refunded_at__isnull=True)
    if membership.plan_price_id is not None:
        queryset = queryset.filter(plan_price_ref=membership.plan_price)
    else:
        queryset = queryset.filter(plan=membership.plan)
    return queryset.order_by("-paid_at", "-created_at").first()


def get_membership_amount_paid(membership):
    last_order = get_last_paid_order(membership)
    if last_order is not None and last_order.total:
        return quantize(last_order.total)
    full_price = membership.effective_full_price
    if full_price:
        return quantize(full_price)
    return Decimal("0.00")


def get_last_paid_order_for_plan(person, plan):
    lookup = (
        {"plan_price_ref": plan} if isinstance(plan, PlanPrice) else {"plan": plan}
    )
    return (
        RegistrationOrder.objects.filter(
            person=person,
            payment_status__in=(PaymentStatus.PAID, PaymentStatus.EXEMPTED),
            total__gt=Decimal("0"),
            **lookup,
        )
        .order_by("-paid_at", "-created_at")
        .first()
    )
