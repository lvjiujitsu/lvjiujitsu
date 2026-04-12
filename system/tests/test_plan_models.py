from decimal import Decimal

from django.test import TestCase

from system.models.plan import BillingCycle, SubscriptionPlan
from system.services.seeding import seed_plans


class SubscriptionPlanModelTestCase(TestCase):
    def test_create_plan(self):
        plan = SubscriptionPlan.objects.create(
            code="test-mensal",
            display_name="Plano Teste",
            price=Decimal("200.00"),
            billing_cycle=BillingCycle.MONTHLY,
        )
        self.assertEqual(str(plan), "Plano Teste")
        self.assertTrue(plan.is_active)

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
    def test_seed_plans_count(self):
        result = seed_plans()
        self.assertEqual(len(result), 3)

    def test_seed_plans_idempotent(self):
        seed_plans()
        seed_plans()
        self.assertEqual(SubscriptionPlan.objects.count(), 3)

    def test_seed_plans_prices(self):
        seed_plans()
        mensal = SubscriptionPlan.objects.get(code="mensal")
        self.assertEqual(mensal.price, Decimal("250.00"))
        irmaos = SubscriptionPlan.objects.get(code="mensal-irmaos")
        self.assertEqual(irmaos.price, Decimal("225.00"))
        trimestral = SubscriptionPlan.objects.get(code="trimestral")
        self.assertEqual(trimestral.price, Decimal("675.00"))
