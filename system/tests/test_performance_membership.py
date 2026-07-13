from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from system.models import Membership, MembershipStatus, Person, PersonType
from system.models.membership import MembershipPauseRequest, MembershipPauseRequestStatus
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanPrice,
    PlanTier,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
from system.services.family_pricing import recompute_family_discounts_for_person
from system.services.membership import resolve_current_pause, resolve_effective_tier


MEMBERSHIP_COUNT = 10


class MembershipTierQueryBudgetTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person_type = PersonType.objects.create(code="student", display_name="Aluno")
        cls.legacy_plan = SubscriptionPlan.objects.create(
            code="legacy-tier-budget",
            display_name="Legado 2x",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            price=Decimal("200.00"),
        )
        cls.tier = PlanTier.objects.create(
            code="adult-2x-tier-budget",
            display_name="Adulto 2x budget",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        cls.plan_price = PlanPrice.objects.create(
            tier=cls.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        PlanTier.objects.create(
            code="adult-2x-tier-budget-legacy-match",
            display_name="Match legado",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        cls.memberships = []
        for index in range(MEMBERSHIP_COUNT):
            person = Person.objects.create(
                full_name=f"Aluno Tier Budget {index:02d}",
                cpf=f"910.000.{index:03d}-{(index % 90) + 1:02d}",
                person_type=cls.person_type,
            )
            if index % 2 == 0:
                membership = Membership.objects.create(
                    person=person,
                    plan_price=cls.plan_price,
                    status=MembershipStatus.ACTIVE,
                )
            else:
                membership = Membership.objects.create(
                    person=person,
                    plan=cls.legacy_plan,
                    status=MembershipStatus.ACTIVE,
                )
            cls.memberships.append(membership)

    def test_resolve_effective_tier_budget_with_shared_cache(self):
        memberships = list(
            Membership.objects.filter(pk__in=[m.pk for m in self.memberships])
            .select_related("plan_price__tier", "plan")
        )
        tier_cache = {}
        with self.assertNumQueries(1):
            tiers = [
                resolve_effective_tier(membership, tier_cache=tier_cache)
                for membership in memberships
            ]
        self.assertEqual(len(tiers), MEMBERSHIP_COUNT)
        self.assertTrue(all(tier is not None for tier in tiers))

    def test_resolve_current_pause_uses_prefetch_without_extra_queries(self):
        membership = self.memberships[0]
        today = timezone.localdate()
        MembershipPauseRequest.objects.create(
            membership=membership,
            status=MembershipPauseRequestStatus.APPROVED,
            requested_start_date=today,
            requested_end_date=today + timedelta(days=7),
        )
        membership = (
            Membership.objects.filter(pk=membership.pk)
            .prefetch_related("pause_requests")
            .first()
        )
        with self.assertNumQueries(0):
            pause = resolve_current_pause(membership)
        self.assertIsNotNone(pause)

    def test_recompute_family_discounts_does_not_n_plus_one_tier_lookup(self):
        owner = self.memberships[0].person
        for membership in self.memberships[1:3]:
            PersonRelationship.objects.get_or_create(
                source_person=owner,
                target_person=membership.person,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            )
        with self.assertNumQueries(14):
            recompute_family_discounts_for_person(owner)
