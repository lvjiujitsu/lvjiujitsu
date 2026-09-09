from django.utils import timezone

from system.business_rule.models.membership import MembershipPauseRequestStatus
from system.business_rule.models.plan import PlanTier


def resolve_effective_tier(membership, tier_cache=None):
    if membership is None:
        return None
    if membership.plan_price_id is not None:
        plan_price = getattr(membership, "plan_price", None)
        if plan_price is not None:
            return plan_price.tier
        return None
    if membership.plan_id is not None and not membership.plan.is_loyalty_plan:

        cache_key = (membership.plan.audience, membership.plan.weekly_frequency)
        if tier_cache is not None and cache_key in tier_cache:
            return tier_cache[cache_key]
        tier = PlanTier.objects.filter(
            audience=membership.plan.audience,
            weekly_frequency=membership.plan.weekly_frequency,
            is_active=True,
        ).first()
        if tier_cache is not None:
            tier_cache[cache_key] = tier
        return tier
    return None


def resolve_current_pause(membership):
    if membership is None:
        return None

    today = timezone.localdate()
    prefetched = getattr(membership, "_prefetched_objects_cache", {})
    if "pause_requests" in prefetched:
        candidates = [
            pause
            for pause in membership.pause_requests.all()
            if pause.status == MembershipPauseRequestStatus.APPROVED
            and pause.requested_start_date <= today
            and pause.requested_end_date >= today
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda pause: pause.requested_end_date)
    return (
        membership.pause_requests.filter(
            status=MembershipPauseRequestStatus.APPROVED,
            requested_start_date__lte=today,
            requested_end_date__gte=today,
        )
        .order_by("-requested_end_date")
        .first()
    )


def membership_is_family_plan(membership):
    if membership is None:
        return False
    if membership.plan_id is not None:
        return membership.plan.is_family_plan
    if membership.plan_price_id is not None:
        tier = resolve_effective_tier(membership)
        if tier is None:
            return False
        tier_code = (tier.code or "").strip().lower()
        return tier_code == "family" or tier_code.startswith("family-")
    return False
