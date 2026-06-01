from django.db.models import Q

from system.models import (
    Membership,
    MembershipStatus,
    PaymentStatus,
    RegistrationOrder,
)
from system.models.plan import SubscriptionPlan


def get_plan_list(filters=None):
    queryset = SubscriptionPlan.objects.order_by(
        "display_order",
        "price",
        "display_name",
    )
    if not filters:
        return queryset

    query = (filters.get("q") or "").strip()
    if query:
        queryset = queryset.filter(
            Q(display_name__icontains=query)
            | Q(code__icontains=query)
            | Q(description__icontains=query)
        )
    if filters.get("audience"):
        queryset = queryset.filter(audience=filters["audience"])
    if filters.get("weekly_frequency"):
        queryset = queryset.filter(weekly_frequency=filters["weekly_frequency"])
    if filters.get("billing_cycle"):
        queryset = queryset.filter(billing_cycle=filters["billing_cycle"])
    if filters.get("payment_method"):
        queryset = queryset.filter(payment_method=filters["payment_method"])
    if filters.get("gateway_code"):
        queryset = queryset.filter(gateway_code=filters["gateway_code"])
    if filters.get("is_active") == "active":
        queryset = queryset.filter(is_active=True)
    elif filters.get("is_active") == "inactive":
        queryset = queryset.filter(is_active=False)
    return queryset


def get_active_plans():
    return SubscriptionPlan.objects.filter(is_active=True).order_by(
        "display_order",
        "price",
        "display_name",
    )


def get_plan_by_pk(pk):
    return SubscriptionPlan.objects.get(pk=pk)


def build_plan_kpis(plans):
    plan_list = list(plans)
    active_count = sum(1 for plan in plan_list if plan.is_active)
    inactive_count = len(plan_list) - active_count
    family_count = sum(1 for plan in plan_list if plan.is_family_plan)
    special_count = sum(
        1 for plan in plan_list if plan.requires_special_authorization
    )
    gateway_count = len(
        {plan.gateway_code for plan in plan_list if plan.gateway_code}
    )
    return [
        {"label": "Total", "value": len(plan_list)},
        {"label": "Ativos", "value": active_count},
        {"label": "Inativos", "value": inactive_count},
        {"label": "Família", "value": family_count},
        {"label": "Especiais", "value": special_count},
        {"label": "Gateways", "value": gateway_count},
    ]


def build_plan_usage(plan):
    memberships = Membership.objects.filter(plan=plan)
    orders = RegistrationOrder.objects.filter(plan=plan)
    return {
        "membership_count": memberships.count(),
        "active_membership_count": memberships.filter(
            status__in=(MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED)
        ).count(),
        "order_count": orders.count(),
        "pending_order_count": orders.filter(
            payment_status=PaymentStatus.PENDING
        ).count(),
    }
