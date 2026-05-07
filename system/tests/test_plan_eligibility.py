from datetime import date
from decimal import Decimal

from django.test import TestCase

from system.constants import RegistrationProfile
from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
from system.selectors.plan_eligibility import (
    PlanEligibilityContext,
    build_eligibility_context_for_registration,
    classify_audience_from_age,
    get_eligible_plans,
    is_plan_eligible,
)
from system.services.seeding import seed_plans


class ClassifyAudienceFromAgeTestCase(TestCase):
    def test_under_eighteen_is_kids_juvenile(self):
        self.assertEqual(
            classify_audience_from_age(
                date(2014, 1, 1), reference_date=date(2026, 1, 2)
            ),
            PlanAudience.KIDS_JUVENILE,
        )

    def test_eighteen_or_older_is_adult(self):
        self.assertEqual(
            classify_audience_from_age(
                date(2000, 1, 1), reference_date=date(2026, 1, 2)
            ),
            PlanAudience.ADULT,
        )

    def test_missing_birth_date_returns_empty(self):
        self.assertEqual(classify_audience_from_age(None), "")


class PlanEligibilityContextTestCase(TestCase):
    def test_adult_alone_does_not_unlock_family(self):
        context = PlanEligibilityContext(adult_active=True, kids_juvenile_active_count=0)
        self.assertFalse(context.adult_family_group_eligible)
        self.assertFalse(context.kids_family_group_eligible)

    def test_adult_with_one_dependent_unlocks_adult_family(self):
        context = PlanEligibilityContext(adult_active=True, kids_juvenile_active_count=1)
        self.assertTrue(context.adult_family_group_eligible)
        self.assertFalse(context.kids_family_group_eligible)

    def test_two_kids_dependents_unlocks_kids_family(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=2)
        self.assertFalse(context.adult_family_group_eligible)
        self.assertTrue(context.kids_family_group_eligible)


class GetEligiblePlansTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_plans()

    def test_adult_alone_only_sees_adult_individual_plans(self):
        context = PlanEligibilityContext(adult_active=True, kids_juvenile_active_count=0)
        plans = get_eligible_plans(context)
        audiences = set(plans.values_list("audience", flat=True))
        family_flags = set(plans.values_list("is_family_plan", flat=True))
        self.assertEqual(audiences, {PlanAudience.ADULT})
        self.assertEqual(family_flags, {False})
        self.assertEqual(plans.count(), 16)

    def test_adult_with_one_dependent_sees_adult_full_set(self):
        context = PlanEligibilityContext(adult_active=True, kids_juvenile_active_count=1)
        plans = get_eligible_plans(context)
        audiences = set(plans.values_list("audience", flat=True))
        self.assertEqual(audiences, {PlanAudience.ADULT, PlanAudience.KIDS_JUVENILE})
        adult_count = plans.filter(audience=PlanAudience.ADULT).count()
        self.assertEqual(adult_count, 32)
        kids_individual_count = plans.filter(
            audience=PlanAudience.KIDS_JUVENILE,
            is_family_plan=False,
        ).count()
        self.assertEqual(kids_individual_count, 8)
        kids_family_count = plans.filter(
            audience=PlanAudience.KIDS_JUVENILE,
            is_family_plan=True,
        ).count()
        self.assertEqual(kids_family_count, 0)

    def test_guardian_with_one_kid_only_sees_kids_individual(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=1)
        plans = get_eligible_plans(context)
        audiences = set(plans.values_list("audience", flat=True))
        family_flags = set(plans.values_list("is_family_plan", flat=True))
        self.assertEqual(audiences, {PlanAudience.KIDS_JUVENILE})
        self.assertEqual(family_flags, {False})
        self.assertEqual(plans.count(), 8)

    def test_guardian_with_two_kids_sees_kids_individual_and_family(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=2)
        plans = get_eligible_plans(context)
        audiences = set(plans.values_list("audience", flat=True))
        self.assertEqual(audiences, {PlanAudience.KIDS_JUVENILE})
        self.assertEqual(plans.count(), 16)

    def test_kids_5x_hidden_unless_authorized(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=2)
        plans = get_eligible_plans(context)
        kids_5x = plans.filter(weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES)
        self.assertEqual(kids_5x.count(), 0)

    def test_kids_5x_visible_when_authorized(self):
        context = PlanEligibilityContext(
            adult_active=False,
            kids_juvenile_active_count=2,
            allow_special_authorization=True,
        )
        plans = get_eligible_plans(context)
        kids_5x = plans.filter(weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES)
        self.assertEqual(kids_5x.count(), 16)

    def test_no_audience_active_returns_empty(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=0)
        plans = get_eligible_plans(context)
        self.assertEqual(plans.count(), 0)


class IsPlanEligibleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_plans()
        cls.adult_individual = SubscriptionPlan.objects.get(
            code="adult-5x-individual-monthly-pix"
        )
        cls.adult_family = SubscriptionPlan.objects.get(
            code="adult-5x-family-monthly-pix"
        )
        cls.kids_individual = SubscriptionPlan.objects.get(
            code="kids_juvenile-2x-individual-monthly-pix"
        )
        cls.kids_family = SubscriptionPlan.objects.get(
            code="kids_juvenile-2x-family-monthly-pix"
        )
        cls.kids_5x_individual = SubscriptionPlan.objects.get(
            code="kids_juvenile-5x-individual-monthly-pix"
        )

    def test_adult_solo_only_individual_adult(self):
        context = PlanEligibilityContext(adult_active=True, kids_juvenile_active_count=0)
        self.assertTrue(is_plan_eligible(self.adult_individual, context))
        self.assertFalse(is_plan_eligible(self.adult_family, context))
        self.assertFalse(is_plan_eligible(self.kids_individual, context))

    def test_adult_with_kid_unlocks_adult_family(self):
        context = PlanEligibilityContext(adult_active=True, kids_juvenile_active_count=1)
        self.assertTrue(is_plan_eligible(self.adult_individual, context))
        self.assertTrue(is_plan_eligible(self.adult_family, context))
        self.assertTrue(is_plan_eligible(self.kids_individual, context))
        self.assertFalse(is_plan_eligible(self.kids_family, context))

    def test_two_kids_unlocks_kids_family(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=2)
        self.assertTrue(is_plan_eligible(self.kids_individual, context))
        self.assertTrue(is_plan_eligible(self.kids_family, context))
        self.assertFalse(is_plan_eligible(self.adult_individual, context))

    def test_kids_5x_blocked_without_authorization(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=2)
        self.assertFalse(is_plan_eligible(self.kids_5x_individual, context))

    def test_kids_5x_allowed_with_authorization(self):
        context = PlanEligibilityContext(
            adult_active=False,
            kids_juvenile_active_count=2,
            allow_special_authorization=True,
        )
        self.assertTrue(is_plan_eligible(self.kids_5x_individual, context))


class BuildEligibilityContextForRegistrationTestCase(TestCase):
    def test_holder_adult_without_dependent(self):
        cleaned_data = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": False,
            "holder_birthdate": date(2000, 1, 1),
            "holder_class_groups": [],
            "extra_dependents": [],
        }
        context = build_eligibility_context_for_registration(cleaned_data)
        self.assertTrue(context.adult_active)
        self.assertEqual(context.kids_juvenile_active_count, 0)

    def test_holder_adult_with_kid_dependent(self):
        cleaned_data = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": True,
            "holder_birthdate": date(1990, 1, 1),
            "holder_class_groups": [],
            "dependent_birthdate": date(2014, 1, 1),
            "dependent_class_groups": [],
            "extra_dependents": [],
        }
        context = build_eligibility_context_for_registration(cleaned_data)
        self.assertTrue(context.adult_active)
        self.assertEqual(context.kids_juvenile_active_count, 1)
        self.assertTrue(context.adult_family_group_eligible)

    def test_guardian_with_two_kids(self):
        cleaned_data = {
            "registration_profile": RegistrationProfile.GUARDIAN,
            "student_birthdate": date(2014, 1, 1),
            "student_class_groups": [],
            "extra_dependents": [
                {
                    "birth_date": date(2016, 5, 5),
                    "class_groups": [],
                },
            ],
        }
        context = build_eligibility_context_for_registration(cleaned_data)
        self.assertFalse(context.adult_active)
        self.assertEqual(context.kids_juvenile_active_count, 2)
        self.assertTrue(context.kids_family_group_eligible)

    def test_guardian_with_one_kid(self):
        cleaned_data = {
            "registration_profile": RegistrationProfile.GUARDIAN,
            "student_birthdate": date(2014, 1, 1),
            "student_class_groups": [],
            "extra_dependents": [],
        }
        context = build_eligibility_context_for_registration(cleaned_data)
        self.assertFalse(context.adult_active)
        self.assertEqual(context.kids_juvenile_active_count, 1)
        self.assertFalse(context.kids_family_group_eligible)
