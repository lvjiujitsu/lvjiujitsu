from decimal import Decimal

from django.test import TestCase

from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
from system.services.seeding import seed_plans


class SubscriptionPlanModelTestCase(TestCase):
    def test_create_plan_uses_defaults(self):
        plan = SubscriptionPlan.objects.create(
            code="test-mensal",
            display_name="Plano Teste",
            price=Decimal("200.00"),
            billing_cycle=BillingCycle.MONTHLY,
        )
        self.assertEqual(str(plan), "Plano Teste")
        self.assertTrue(plan.is_active)
        self.assertEqual(plan.audience, PlanAudience.ADULT)
        self.assertEqual(plan.weekly_frequency, PlanWeeklyFrequency.FIVE_TIMES)
        self.assertEqual(plan.teacher_commission_percentage, Decimal("0.00"))
        self.assertFalse(plan.requires_special_authorization)

    def test_unique_code(self):
        SubscriptionPlan.objects.create(
            code="unique-test",
            display_name="Plano A",
            price=Decimal("100.00"),
        )
        with self.assertRaises(Exception):
            SubscriptionPlan.objects.create(
                code="unique-test",
                display_name="Plano B",
                price=Decimal("200.00"),
            )

    def test_ordering(self):
        SubscriptionPlan.objects.create(
            code="z-plan", display_name="Caro",
            price=Decimal("500.00"), display_order=2,
        )
        SubscriptionPlan.objects.create(
            code="a-plan", display_name="Barato",
            price=Decimal("100.00"), display_order=1,
        )
        plans = list(SubscriptionPlan.objects.all())
        self.assertEqual(plans[0].code, "a-plan")
        self.assertEqual(plans[1].code, "z-plan")


class SeedPlansTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.result = seed_plans()

    def test_seed_plans_creates_full_matrix(self):
        self.assertEqual(len(self.result), 64)

    def test_seed_plans_idempotent(self):
        seed_plans()
        self.assertEqual(SubscriptionPlan.objects.count(), 64)

    def test_seed_plans_audience_distribution(self):
        self.assertEqual(
            SubscriptionPlan.objects.filter(audience=PlanAudience.ADULT).count(),
            32,
        )
        self.assertEqual(
            SubscriptionPlan.objects.filter(audience=PlanAudience.KIDS_JUVENILE).count(),
            32,
        )

    def test_seed_plans_frequency_distribution(self):
        self.assertEqual(
            SubscriptionPlan.objects.filter(
                weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES
            ).count(),
            32,
        )
        self.assertEqual(
            SubscriptionPlan.objects.filter(
                weekly_frequency=PlanWeeklyFrequency.TWICE
            ).count(),
            32,
        )

    def test_seed_plans_family_distribution(self):
        self.assertEqual(
            SubscriptionPlan.objects.filter(is_family_plan=True).count(), 32
        )
        self.assertEqual(
            SubscriptionPlan.objects.filter(is_family_plan=False).count(), 32
        )

    def test_kids_juvenile_carries_teacher_commission(self):
        kids_plans = SubscriptionPlan.objects.filter(audience=PlanAudience.KIDS_JUVENILE)
        for plan in kids_plans:
            self.assertEqual(plan.teacher_commission_percentage, Decimal("50.00"))

    def test_adult_plans_have_zero_teacher_commission(self):
        adult_plans = SubscriptionPlan.objects.filter(audience=PlanAudience.ADULT)
        for plan in adult_plans:
            self.assertEqual(plan.teacher_commission_percentage, Decimal("0.00"))

    def test_kids_5x_requires_special_authorization(self):
        kids_5x = SubscriptionPlan.objects.filter(
            audience=PlanAudience.KIDS_JUVENILE,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
        )
        self.assertEqual(kids_5x.count(), 16)
        for plan in kids_5x:
            self.assertTrue(plan.requires_special_authorization)

    def test_other_plans_do_not_require_authorization(self):
        other_plans = SubscriptionPlan.objects.exclude(
            audience=PlanAudience.KIDS_JUVENILE,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
        )
        for plan in other_plans:
            self.assertFalse(plan.requires_special_authorization)

    def test_adult_5x_individual_pix_monthly_pricing(self):
        plan = SubscriptionPlan.objects.get(code="adult-5x-individual-monthly-pix")
        self.assertEqual(plan.price, Decimal("257.00"))
        self.assertEqual(plan.monthly_reference_price, Decimal("257.00"))
        self.assertEqual(plan.payment_method, PlanPaymentMethod.PIX)
        self.assertEqual(plan.audience, PlanAudience.ADULT)
        self.assertEqual(plan.weekly_frequency, PlanWeeklyFrequency.FIVE_TIMES)
        self.assertFalse(plan.is_family_plan)

    def test_adult_5x_individual_credit_annual_pricing(self):
        plan = SubscriptionPlan.objects.get(code="adult-5x-individual-annual-credit-card")
        self.assertEqual(plan.price, Decimal("3204.00"))
        self.assertEqual(plan.monthly_reference_price, Decimal("267.00"))

    def test_adult_2x_family_pix_quarterly_pricing(self):
        plan = SubscriptionPlan.objects.get(code="adult-2x-family-quarterly-pix")
        self.assertEqual(plan.price, Decimal("636.00"))
        self.assertEqual(plan.monthly_reference_price, Decimal("212.00"))
        self.assertTrue(plan.is_family_plan)

    def test_kids_2x_individual_pix_monthly_pricing(self):
        plan = SubscriptionPlan.objects.get(code="kids_juvenile-2x-individual-monthly-pix")
        self.assertEqual(plan.price, Decimal("424.00"))
        self.assertEqual(plan.monthly_reference_price, Decimal("424.00"))
        self.assertEqual(plan.audience, PlanAudience.KIDS_JUVENILE)

    def test_kids_5x_family_credit_semiannual_pricing(self):
        plan = SubscriptionPlan.objects.get(code="kids_juvenile-5x-family-semiannual-credit-card")
        self.assertEqual(plan.price, Decimal("2940.00"))
        self.assertEqual(plan.monthly_reference_price, Decimal("490.00"))
        self.assertTrue(plan.requires_special_authorization)

    def test_cycle_price_is_monthly_times_months(self):
        monthly = SubscriptionPlan.objects.get(code="adult-5x-individual-monthly-pix")
        quarterly = SubscriptionPlan.objects.get(code="adult-5x-individual-quarterly-pix")
        semiannual = SubscriptionPlan.objects.get(code="adult-5x-individual-semiannual-pix")
        annual = SubscriptionPlan.objects.get(code="adult-5x-individual-annual-pix")
        self.assertEqual(quarterly.price, monthly.price * 3)
        self.assertEqual(semiannual.price, monthly.price * 6)
        self.assertEqual(annual.price, monthly.price * 12)

    def test_seed_deactivates_legacy_plans(self):
        legacy = SubscriptionPlan.objects.create(
            code="legacy-mensal-pix",
            display_name="Plano Legado",
            price=Decimal("240.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
        )
        seed_plans()
        legacy.refresh_from_db()
        self.assertFalse(legacy.is_active)

    def test_pix_monthly_reference_matches_business_rule(self):
        expected_pix_monthly = {
            ("adult", PlanWeeklyFrequency.TWICE, True): Decimal("212.00"),
            ("adult", PlanWeeklyFrequency.TWICE, False): Decimal("222.00"),
            ("adult", PlanWeeklyFrequency.FIVE_TIMES, True): Decimal("237.00"),
            ("adult", PlanWeeklyFrequency.FIVE_TIMES, False): Decimal("257.00"),
            ("kids_juvenile", PlanWeeklyFrequency.TWICE, True): Decimal("404.00"),
            ("kids_juvenile", PlanWeeklyFrequency.TWICE, False): Decimal("424.00"),
            ("kids_juvenile", PlanWeeklyFrequency.FIVE_TIMES, True): Decimal("454.00"),
            ("kids_juvenile", PlanWeeklyFrequency.FIVE_TIMES, False): Decimal("484.00"),
        }
        for (audience, frequency, is_family), expected_price in expected_pix_monthly.items():
            plan = SubscriptionPlan.objects.get(
                audience=audience,
                weekly_frequency=frequency,
                is_family_plan=is_family,
                billing_cycle=BillingCycle.MONTHLY,
                payment_method=PlanPaymentMethod.PIX,
            )
            self.assertEqual(
                plan.price,
                expected_price,
                msg=f"PIX mensal {audience}/{int(frequency)}x/{'familia' if is_family else 'individual'}",
            )

    def test_credit_monthly_reference_matches_business_rule(self):
        expected_credit_monthly = {
            ("adult", PlanWeeklyFrequency.TWICE, True): Decimal("220.00"),
            ("adult", PlanWeeklyFrequency.TWICE, False): Decimal("230.00"),
            ("adult", PlanWeeklyFrequency.FIVE_TIMES, True): Decimal("246.00"),
            ("adult", PlanWeeklyFrequency.FIVE_TIMES, False): Decimal("267.00"),
            ("kids_juvenile", PlanWeeklyFrequency.TWICE, True): Decimal("436.00"),
            ("kids_juvenile", PlanWeeklyFrequency.TWICE, False): Decimal("458.00"),
            ("kids_juvenile", PlanWeeklyFrequency.FIVE_TIMES, True): Decimal("490.00"),
            ("kids_juvenile", PlanWeeklyFrequency.FIVE_TIMES, False): Decimal("523.00"),
        }
        for (audience, frequency, is_family), expected_price in expected_credit_monthly.items():
            plan = SubscriptionPlan.objects.get(
                audience=audience,
                weekly_frequency=frequency,
                is_family_plan=is_family,
                billing_cycle=BillingCycle.MONTHLY,
                payment_method=PlanPaymentMethod.CREDIT_CARD,
            )
            self.assertEqual(
                plan.price,
                expected_price,
                msg=f"Cartão mensal {audience}/{int(frequency)}x/{'familia' if is_family else 'individual'}",
            )
