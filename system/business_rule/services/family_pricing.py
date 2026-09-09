import logging
from collections import defaultdict

from django.db import transaction

from system.business_rule.models.membership import Membership, MembershipStatus
from system.business_rule.models.membership_timeline import MembershipTimelineEventType
from system.business_rule.selectors.plan_eligibility import get_family_group_members
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.services.membership_resolution import resolve_effective_tier
from system.business_rule.services.stripe_discounts import (
    StripeDiscountError,
    apply_family_discount,
    remove_family_discount,
)


logger = logging.getLogger(__name__)


@transaction.atomic
def recompute_family_discounts_for_person(person):
    if person is None:
        return []

    members = get_family_group_members(person)
    memberships = (
        Membership.objects.filter(person__in=members)
        .exclude(status__in=(MembershipStatus.CANCELED, MembershipStatus.EXPIRED))
        .exclude(plan_price__isnull=True, plan__isnull=True)
        .exclude(plan__is_loyalty_plan=True)
        .select_related("plan_price__tier", "plan")
    )

    by_tier = defaultdict(list)
    tier_cache = {}
    for membership in memberships:
        tier = resolve_effective_tier(membership, tier_cache=tier_cache)
        if tier is None:
            continue
        by_tier[tier.pk].append(membership)

    changed = []
    for tier_memberships in by_tier.values():
        discount_applies = len(tier_memberships) >= 2
        for membership in tier_memberships:
            previous = membership.family_discount_applied
            previous_price = membership.billed_price
            membership.family_discount_applied = discount_applies
            membership.recompute_billed_price(
                tier=resolve_effective_tier(membership, tier_cache=tier_cache)
            )
            membership.save(
                update_fields=["family_discount_applied", "billed_price", "updated_at"]
            )
            if previous != discount_applies:
                changed.append(membership)
                _sync_stripe_discount(membership, discount_applies)
                record_membership_event(
                    membership.person,
                    MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED,
                    membership=membership,
                    actor=None,
                    context={
                        "discount_applied": discount_applies,
                        "old_price": str(previous_price) if previous_price is not None else "",
                        "new_price": str(membership.billed_price)
                        if membership.billed_price is not None
                        else "",
                    },
                )

    return changed


def _sync_stripe_discount(membership, discount_applies):
    if not membership.stripe_subscription_id:
        return
    try:
        if discount_applies:
            apply_family_discount(membership)
        else:
            remove_family_discount(membership)
    except StripeDiscountError:
        logger.exception(
            "recompute_family_discounts_for_person: falha ao sincronizar desconto "
            "Stripe (membership=%s).",
            membership.pk,
        )
    except Exception:
        logger.exception(
            "recompute_family_discounts_for_person: erro inesperado ao sincronizar "
            "desconto Stripe (membership=%s).",
            membership.pk,
        )
