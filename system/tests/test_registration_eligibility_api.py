import json
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from system.constants import RegistrationProfile
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanPrice, PlanTier, PlanWeeklyFrequency
from system.selectors.plan_eligibility import (
    build_eligibility_context_for_registration,
    get_eligible_plan_prices,
)
from system.services.registration_checkout import CATALOG_ID_PREFIX_PLAN_PRICE, build_catalog_plan_id


class RegistrationEligibilityApiContractTestCase(TestCase):
    def setUp(self):
        self.adult_tier = PlanTier.objects.create(
            code="adult-2x-eligibility-api",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.adult_family_tier = PlanTier.objects.create(
            code="adult-2x-family-eligibility-api",
            display_name="Adulto 2x por semana (família)",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("10.00"),
        )
        self.kids_tier = PlanTier.objects.create(
            code="kids-2x-eligibility-api",
            display_name="Kids 2x por semana",
            audience=PlanAudience.KIDS_JUVENILE,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.adult_price = PlanPrice.objects.create(
            tier=self.adult_tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.kids_price = PlanPrice.objects.create(
            tier=self.kids_tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("180.00"),
        )

    def _post_eligibility(self, payload):
        return self.client.post(
            reverse("system:registration-eligibility"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_holder_adult_alone_matches_selector_directly(self):
        payload = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": "01/01/2000",
        }
        response = self._post_eligibility(payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()

        cleaned_data = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": date(2000, 1, 1),
            "holder_class_groups": [],
            "extra_dependents": [],
        }
        expected_context = build_eligibility_context_for_registration(cleaned_data)
        expected_ids = [
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, plan_price.pk)
            for plan_price in get_eligible_plan_prices(expected_context)
        ]

        self.assertEqual(set(body["eligible_plan_ids"]), set(expected_ids))
        self.assertIn(build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, self.adult_price.pk), body["eligible_plan_ids"])
        self.assertNotIn(build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, self.kids_price.pk), body["eligible_plan_ids"])
        self.assertTrue(body["context"]["adult_active"])
        self.assertEqual(body["context"]["kids_juvenile_active_count"], 0)
        self.assertFalse(body["context"]["adult_family_group_eligible"])

    def test_holder_adult_with_kid_dependent_matches_selector_directly(self):
        payload = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": True,
            "holder_birthdate": "01/01/1990",
            "dependent_birthdate": "01/01/2014",
        }
        response = self._post_eligibility(payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()

        cleaned_data = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": True,
            "holder_birthdate": date(1990, 1, 1),
            "holder_class_groups": [],
            "dependent_birthdate": date(2014, 1, 1),
            "dependent_class_groups": [],
            "extra_dependents": [],
        }
        expected_context = build_eligibility_context_for_registration(cleaned_data)
        expected_ids = [
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, plan_price.pk)
            for plan_price in get_eligible_plan_prices(expected_context)
        ]

        self.assertEqual(set(body["eligible_plan_ids"]), set(expected_ids))
        self.assertTrue(body["context"]["adult_active"])
        self.assertEqual(body["context"]["kids_juvenile_active_count"], 1)
        self.assertTrue(body["context"]["adult_family_group_eligible"])

    def test_holder_birthdate_accepts_iso_format(self):
        payload = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": "2000-01-01",
        }
        response = self._post_eligibility(payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["context"]["adult_active"])
        self.assertIn(
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, self.adult_price.pk),
            body["eligible_plan_ids"],
        )

    def test_no_data_returns_empty_eligibility(self):
        response = self._post_eligibility({})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["eligible_plan_ids"], [])
        self.assertFalse(body["context"]["adult_active"])
        self.assertEqual(body["context"]["kids_juvenile_active_count"], 0)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            reverse("system:registration-eligibility"),
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_requires_post(self):
        response = self.client.get(reverse("system:registration-eligibility"))
        self.assertEqual(response.status_code, 405)
