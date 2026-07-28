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
        self.assertFalse(plan.is_loyalty_plan)
        self.assertFalse(plan.is_family_plan)

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

    def test_compute_price_pix_monthly(self):
        plan = SubscriptionPlan.objects.create(
            code="individual-2x-pix-m",
            display_name="Individual 2x PIX Mensal",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("220.00"),
            gateway_fixed_fee=Decimal("1.99"),
            gateway_percentage_fee=Decimal("0.0000"),
            cycle_discount_percentage=Decimal("0.0000"),
        )
        self.assertEqual(plan.price, Decimal("221.99"))
        self.assertIsNone(plan.monthly_reference_price)

    def test_compute_price_asaas_card_monthly(self):
        plan = SubscriptionPlan.objects.create(
            code="individual-2x-asaas-card-m",
            display_name="Individual 2x Cartão Mensal",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("220.00"),
            gateway_fixed_fee=Decimal("0.49"),
            gateway_percentage_fee=Decimal("0.0429"),
            cycle_discount_percentage=Decimal("0.0000"),
        )
        self.assertEqual(plan.price, Decimal("230.37"))

    def test_compute_price_pix_quarterly_sets_monthly_reference(self):
        plan = SubscriptionPlan.objects.create(
            code="individual-2x-pix-q",
            display_name="Individual 2x PIX Trimestral",
            billing_cycle=BillingCycle.QUARTERLY,
            base_monthly_net_price=Decimal("220.00"),
            gateway_fixed_fee=Decimal("1.99"),
            gateway_percentage_fee=Decimal("0.0000"),
            cycle_discount_percentage=Decimal("0.0257"),
        )
        self.assertIsNotNone(plan.monthly_reference_price)
        self.assertEqual(plan.monthly_reference_price, (plan.price / 3).quantize(Decimal("0.01")))

    def test_compute_price_annual_5x_pix(self):
        plan = SubscriptionPlan.objects.create(
            code="individual-5x-pix-a",
            display_name="Individual 5x PIX Anual",
            billing_cycle=BillingCycle.ANNUAL,
            base_monthly_net_price=Decimal("250.00"),
            gateway_fixed_fee=Decimal("1.99"),
            gateway_percentage_fee=Decimal("0.0000"),
            cycle_discount_percentage=Decimal("0.1200"),
        )
        self.assertEqual(plan.price, Decimal("2641.99"))

    def test_plan_without_base_net_keeps_manual_price(self):
        plan = SubscriptionPlan.objects.create(
            code="manual-price",
            display_name="Preço Manual",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("199.90"),
        )
        self.assertEqual(plan.price, Decimal("199.90"))

    def test_recomputes_on_update(self):
        plan = SubscriptionPlan.objects.create(
            code="update-test",
            display_name="Recalcula ao editar",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("220.00"),
            gateway_fixed_fee=Decimal("1.99"),
            gateway_percentage_fee=Decimal("0.0000"),
            cycle_discount_percentage=Decimal("0.0000"),
        )
        self.assertEqual(plan.price, Decimal("221.99"))

        plan.gateway_fixed_fee = Decimal("2.49")
        plan.save()
        self.assertEqual(plan.price, Decimal("222.49"))
