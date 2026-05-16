from decimal import Decimal

from django.test import TestCase

from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
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



