from datetime import date

from django.test import TestCase

from system.constants import RegistrationProfile
from system.models.plan import PlanAudience
from system.selectors.plan_eligibility import (
    PlanEligibilityContext,
    build_eligibility_context_for_registration,
    classify_audience_from_age,
)
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

    def test_two_adults_unlock_adult_family(self):
        context = PlanEligibilityContext(
            adult_active=True,
            adult_active_count=2,
            kids_juvenile_active_count=0,
        )
        self.assertTrue(context.adult_family_group_eligible)
        self.assertFalse(context.kids_family_group_eligible)

    def test_two_kids_dependents_unlocks_kids_family(self):
        context = PlanEligibilityContext(adult_active=False, kids_juvenile_active_count=2)
        self.assertFalse(context.adult_family_group_eligible)
        self.assertTrue(context.kids_family_group_eligible)


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

    def test_holder_adult_with_adult_dependent_unlocks_adult_family(self):
        cleaned_data = {
            "registration_profile": RegistrationProfile.HOLDER,
            "include_dependent": True,
            "holder_birthdate": date(1990, 1, 1),
            "holder_class_groups": [],
            "dependent_birthdate": date(2001, 1, 1),
            "dependent_class_groups": [],
            "extra_dependents": [],
        }
        context = build_eligibility_context_for_registration(cleaned_data)
        self.assertEqual(context.adult_active_count, 2)
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
