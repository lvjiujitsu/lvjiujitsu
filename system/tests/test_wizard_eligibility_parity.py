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


class WizardEligibilityParityTestCase(TestCase):
    def setUp(self):
        self.adult_tier = PlanTier.objects.create(
            code="parity-adult-2x",
            display_name="Adulto 2x",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.kids_tier = PlanTier.objects.create(
            code="parity-kids-2x",
            display_name="Kids 2x",
            audience=PlanAudience.KIDS_JUVENILE,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.adult_price = PlanPrice.objects.create(
            tier=self.adult_tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.kids_price = PlanPrice.objects.create(
            tier=self.kids_tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("180.00"),
        )

    def _expected_ids(self, cleaned_data):
        context = build_eligibility_context_for_registration(cleaned_data)
        return {
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, plan_price.pk)
            for plan_price in get_eligible_plan_prices(context)
        }

    def _assert_api_matches_selector(self, payload, cleaned_data):
        response = self.client.post(
            reverse("system:registration-eligibility"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body["eligible_plan_ids"]), self._expected_ids(cleaned_data))

    def test_holder_adult_parity(self):
        payload = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": "15/07/2000",
        }
        cleaned = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": date(2000, 7, 15),
            "holder_class_groups": [],
            "extra_dependents": [],
        }
        self._assert_api_matches_selector(payload, cleaned)
        self.assertIn(
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, self.adult_price.pk),
            self._expected_ids(cleaned),
        )

    def test_guardian_child_parity(self):
        payload = {
            "registration_profile": RegistrationProfile.GUARDIAN,
            "student_birthdate": "15/07/2015",
            "extra_dependents": [],
        }
        cleaned = {
            "registration_profile": RegistrationProfile.GUARDIAN,
            "student_birthdate": date(2015, 7, 15),
            "student_class_groups": [],
            "extra_dependents": [],
        }
        self._assert_api_matches_selector(payload, cleaned)
        self.assertIn(
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, self.kids_price.pk),
            self._expected_ids(cleaned),
        )

    def test_dependent_wizard_payload_parity(self):
        payload = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": "15/07/2015",
            "holder_class_groups": [],
        }
        cleaned = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": date(2015, 7, 15),
            "holder_class_groups": [],
            "extra_dependents": [],
        }
        self._assert_api_matches_selector(payload, cleaned)
        self.assertIn(
            build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, self.kids_price.pk),
            self._expected_ids(cleaned),
        )
