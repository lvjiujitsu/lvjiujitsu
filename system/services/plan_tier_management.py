from django.db.models import Q

from system.models.membership import Membership, MembershipStatus
from system.models.plan import PlanPrice, PlanTier


def get_plan_tier_list(filters=None):
    queryset = PlanTier.objects.order_by("display_order", "display_name")
    if not filters:
        return queryset

    query = (filters.get("q") or "").strip()
    if query:
        queryset = queryset.filter(
            Q(display_name__icontains=query) | Q(code__icontains=query)
        )
    if filters.get("audience"):
        queryset = queryset.filter(audience=filters["audience"])
    if filters.get("weekly_frequency"):
        queryset = queryset.filter(weekly_frequency=filters["weekly_frequency"])
    if filters.get("is_active") == "active":
        queryset = queryset.filter(is_active=True)
    elif filters.get("is_active") == "inactive":
        queryset = queryset.filter(is_active=False)
    return queryset


def get_plan_tier_by_pk(pk):
    return PlanTier.objects.get(pk=pk)


def build_plan_tier_kpis(tiers):
    tier_list = list(tiers)
    active_count = sum(1 for tier in tier_list if tier.is_active)
    inactive_count = len(tier_list) - active_count
    price_count = PlanPrice.objects.filter(tier__in=tier_list).count()
    return [
        {"label": "Total", "value": len(tier_list)},
        {"label": "Ativos", "value": active_count},
        {"label": "Inativos", "value": inactive_count},
        {"label": "Preços cadastrados", "value": price_count},
    ]


def build_plan_tier_usage(tier):
    prices = PlanPrice.objects.filter(tier=tier)
    memberships = Membership.objects.filter(plan_price__tier=tier)
    return {
        "price_count": prices.count(),
        "active_price_count": prices.filter(is_active=True).count(),
        "membership_count": memberships.count(),
        "active_membership_count": memberships.filter(
            status__in=(MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED)
        ).count(),
    }


def get_plan_price_by_pk(pk):
    return PlanPrice.objects.select_related("tier").get(pk=pk)


def build_plan_price_usage(plan_price):
    memberships = Membership.objects.filter(plan_price=plan_price)
    return {
        "membership_count": memberships.count(),
        "active_membership_count": memberships.filter(
            status__in=(MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED)
        ).count(),
    }
