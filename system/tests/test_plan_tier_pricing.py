from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PlanPrice,
    PlanTier,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency


class PlanTierTestCase(TestCase):
    def test_creates_tier_with_family_discount(self):
        tier = PlanTier.objects.create(
            code="adult-2x",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )

        self.assertEqual(tier.family_discount_percentage, Decimal("0.18"))
        self.assertTrue(tier.is_active)


class PlanPriceComputationTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-pricing",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )

    def test_price_computed_with_gateway_fixed_fee(self):
        price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            gateway_code="asaas_pix",
            base_monthly_net_price=Decimal("200.00"),
            gateway_fixed_fee=Decimal("1.99"),
        )

        self.assertEqual(price.price, Decimal("201.99"))

    def test_price_computed_with_gateway_percentage_fee(self):
        price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            billing_cycle=BillingCycle.MONTHLY,
            gateway_code="asaas_card",
            base_monthly_net_price=Decimal("200.00"),
            gateway_fixed_fee=Decimal("0.49"),
            gateway_percentage_fee=Decimal("0.0429"),
        )

        expected = ((Decimal("200.00") + Decimal("0.49")) / (1 - Decimal("0.0429"))).quantize(
            Decimal("0.01")
        )
        self.assertEqual(price.price, expected)

    def test_monthly_reference_price_set_for_multi_month_cycles(self):
        price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.QUARTERLY,
            base_monthly_net_price=Decimal("200.00"),
        )

        self.assertIsNotNone(price.monthly_reference_price)
        self.assertEqual(price.monthly_reference_price, (price.price / 3).quantize(Decimal("0.01")))

    def test_family_price_applies_tier_discount(self):
        price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )

        self.assertEqual(price.family_price(), (price.price * Decimal("0.82")).quantize(Decimal("0.01")))

    def test_price_recomputed_via_update_or_create_persists_to_database(self):
        PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            gateway_code="asaas_pix",
            base_monthly_net_price=Decimal("200.00"),
            gateway_fixed_fee=Decimal("1.99"),
        )

        price, created = PlanPrice.objects.update_or_create(
            tier=self.tier,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            defaults={
                "payment_method": PlanPaymentMethod.PIX,
                "base_monthly_net_price": Decimal("300.00"),
                "gateway_fixed_fee": Decimal("1.99"),
            },
        )

        self.assertFalse(created)
        self.assertEqual(price.price, Decimal("301.99"))
        persisted = PlanPrice.objects.get(pk=price.pk)
        self.assertEqual(persisted.price, Decimal("301.99"))


class PlanPriceImmutabilityTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-immutable",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Pessoa PlanPrice Imutavel",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def test_editing_pricing_fields_allowed_when_not_referenced(self):
        self.price.base_monthly_net_price = Decimal("210.00")
        self.price.save()

        self.price.refresh_from_db()
        self.assertEqual(self.price.base_monthly_net_price, Decimal("210.00"))

    def test_editing_pricing_fields_raises_when_referenced_by_membership(self):
        Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        self.price.base_monthly_net_price = Decimal("999.00")
        with self.assertRaises(ValueError):
            self.price.save()

    def test_archiving_referenced_price_is_allowed(self):
        Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        self.price.archive()

        self.price.refresh_from_db()
        self.assertFalse(self.price.is_active)
        self.assertIsNotNone(self.price.effective_until)


class MembershipPlanPriceTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-membership",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Pessoa Membership PlanPrice",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def test_membership_can_reference_plan_price_without_legacy_plan(self):
        membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        self.assertIsNone(membership.plan_id)
        self.assertEqual(membership.plan_price_id, self.price.pk)

    def test_recompute_billed_price_without_family_discount(self):
        membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        membership.recompute_billed_price()

        self.assertEqual(membership.billed_price, self.price.price)

    def test_recompute_billed_price_with_family_discount(self):
        membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            family_discount_applied=True,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        membership.recompute_billed_price()

        self.assertEqual(membership.billed_price, self.price.family_price())
