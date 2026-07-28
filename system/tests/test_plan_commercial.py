from decimal import Decimal

from django.test import TestCase

from system.models import PlanPrice, PlanTier, SubscriptionPlan
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services.registration_checkout import get_plan_catalog_payload
from system.utils.plan_commercial import (
    COMMERCIAL_TIER_FAMILY,
    COMMERCIAL_TIER_FIDELITY,
    COMMERCIAL_TIER_INDIVIDUAL,
    resolve_commercial_tier,
)


class ResolveCommercialTierTestCase(TestCase):
    def test_family_plan_is_family_tier(self):
        self.assertEqual(
            resolve_commercial_tier(is_family_plan=True, is_loyalty_plan=False),
            COMMERCIAL_TIER_FAMILY,
        )

    def test_loyalty_plan_is_fidelity_tier(self):
        self.assertEqual(
            resolve_commercial_tier(is_family_plan=False, is_loyalty_plan=True),
            COMMERCIAL_TIER_FIDELITY,
        )

    def test_family_takes_precedence_over_loyalty(self):
        self.assertEqual(
            resolve_commercial_tier(is_family_plan=True, is_loyalty_plan=True),
            COMMERCIAL_TIER_FAMILY,
        )

    def test_plain_plan_is_individual_tier(self):
        self.assertEqual(
            resolve_commercial_tier(is_family_plan=False, is_loyalty_plan=False),
            COMMERCIAL_TIER_INDIVIDUAL,
        )


class PlanCatalogPayloadCommercialTierTestCase(TestCase):
    def test_real_loyalty_plan_code_resolves_to_fidelity_tier(self):
        SubscriptionPlan.objects.create(
            code="loyalty-2x-asaas-pix-monthly",
            display_name="Veterano 2x por semana - Asaas PIX - Mensal",
            price=Decimal("205.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_loyalty_plan=True,
            is_active=True,
        )

        payload = get_plan_catalog_payload()

        loyalty_entry = next(p for p in payload if p["code"] == "loyalty-2x-asaas-pix-monthly")
        self.assertEqual(loyalty_entry["commercial_tier"], COMMERCIAL_TIER_FIDELITY)
        self.assertEqual(loyalty_entry["commercial_tier_label"], "Veterano")

    def test_real_family_plan_code_resolves_to_family_tier(self):
        SubscriptionPlan.objects.create(
            code="family-2x-asaas-pix-monthly",
            display_name="Família 2x por semana - Asaas PIX - Mensal",
            price=Decimal("205.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_family_plan=True,
            is_active=True,
        )

        payload = get_plan_catalog_payload()

        family_entry = next(p for p in payload if p["code"] == "family-2x-asaas-pix-monthly")
        self.assertEqual(family_entry["commercial_tier"], COMMERCIAL_TIER_FAMILY)
        self.assertEqual(family_entry["commercial_tier_label"], "Família")


class PlanPriceCatalogMultiGatewayCardPriceTestCase(TestCase):

    def test_asaas_card_and_stripe_card_report_their_own_price(self):
        tier = PlanTier.objects.create(
            code="adult-2x-catalog-multigateway",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        PlanPrice.objects.create(
            tier=tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="asaas_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("225.00"),
            gateway_fixed_fee=Decimal("0.49"),
            gateway_percentage_fee=Decimal("0.0429"),
        )
        PlanPrice.objects.create(
            tier=tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("225.00"),
            gateway_fixed_fee=Decimal("0.39"),
            gateway_percentage_fee=Decimal("0.0399"),
        )

        payload = get_plan_catalog_payload(include_plan_prices=True)

        asaas_entry = next(p for p in payload if p["gateway_code"] == "asaas_card")
        stripe_entry = next(p for p in payload if p["gateway_code"] == "stripe_card")

        self.assertEqual(asaas_entry["charge_card"], asaas_entry["price"])
        self.assertEqual(stripe_entry["charge_card"], stripe_entry["price"])
        self.assertNotEqual(asaas_entry["price"], stripe_entry["price"])
        self.assertNotEqual(asaas_entry["charge_card"], stripe_entry["charge_card"])
