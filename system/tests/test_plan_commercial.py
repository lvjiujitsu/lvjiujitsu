from decimal import Decimal

from django.test import TestCase

from system.models import SubscriptionPlan
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod
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
