from django.test import TestCase

from system.forms import PersonForm, PlanForm, PortalRegistrationForm
from system.models import BiologicalSex


class PortalRegistrationFormMartialArtTestCase(TestCase):
    def test_clears_martial_art_details_when_answer_is_no(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Aluno Sem Historico",
                "holder_cpf": "12345678915",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "holder_has_martial_art": "no",
                "holder_martial_art": "jiu_jitsu",
                "holder_martial_art_graduation": "Faixa cinza",
                "holder_jiu_jitsu_belt": "blue",
                "holder_jiu_jitsu_stripes": "2",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["holder_martial_art"], "")
        self.assertEqual(form.cleaned_data["holder_martial_art_graduation"], "")
        self.assertEqual(form.cleaned_data["holder_jiu_jitsu_belt"], "")
        self.assertIsNone(form.cleaned_data["holder_jiu_jitsu_stripes"])

    def test_requires_martial_art_when_answer_is_yes(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Aluno Com Historico",
                "holder_cpf": "12345678916",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "holder_has_martial_art": "yes",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("holder_martial_art", form.errors)


class PersonFormLayoutContractTestCase(TestCase):
    def test_exposes_fields_grouped_by_people_screen_contract(self):
        form = PersonForm()

        self.assertEqual(
            [field.name for field in form.identity_fields],
            [
                "full_name",
                "cpf",
                "email",
                "phone",
                "birth_date",
                "biological_sex",
            ],
        )
        self.assertEqual(
            [field.name for field in form.health_fields],
            ["blood_type", "allergies", "previous_injuries", "emergency_contact"],
        )
        self.assertEqual(
            [field.name for field in form.martial_art_fields],
            [
                "has_martial_art",
                "martial_art",
                "martial_art_graduation",
                "jiu_jitsu_belt",
                "jiu_jitsu_stripes",
                "martial_art_started_at",
                "martial_art_last_graduation_at",
                "previous_academy",
            ],
        )
        self.assertEqual(
            [field.name for field in form.relationship_fields],
            ["person_type", "class_groups", "is_active"],
        )

    def test_clears_person_martial_art_history_when_answer_is_no(self):
        form = PersonForm(
            data={
                "full_name": "Aluno Sem Tatame",
                "cpf": "12345678915",
                "email": "",
                "phone": "",
                "birth_date": "",
                "biological_sex": "",
                "blood_type": "",
                "allergies": "",
                "previous_injuries": "",
                "emergency_contact": "",
                "has_martial_art": "no",
                "martial_art": "jiu_jitsu",
                "martial_art_graduation": "Roxa",
                "jiu_jitsu_belt": "purple",
                "jiu_jitsu_stripes": "2",
                "martial_art_started_at": "2020-01-01",
                "martial_art_last_graduation_at": "2025-01-01",
                "previous_academy": "Academia anterior",
                "person_type": "",
                "class_groups": [],
                "is_active": "on",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.cleaned_data["martial_art"], "")
        self.assertEqual(form.cleaned_data["martial_art_graduation"], "")
        self.assertEqual(form.cleaned_data["jiu_jitsu_belt"], "")
        self.assertIsNone(form.cleaned_data["jiu_jitsu_stripes"])
        self.assertIsNone(form.cleaned_data["martial_art_started_at"])
        self.assertIsNone(form.cleaned_data["martial_art_last_graduation_at"])
        self.assertEqual(form.cleaned_data["previous_academy"], "")


class PlanFormLayoutContractTestCase(TestCase):
    def test_exposes_fields_grouped_by_plan_screen_contract(self):
        form = PlanForm()

        self.assertEqual(
            [field.name for field in form.identity_fields],
            ["code", "display_name", "description", "display_order", "is_active"],
        )
        self.assertEqual(
            [field.name for field in form.segmentation_fields],
            [
                "audience",
                "weekly_frequency",
                "billing_cycle",
                "payment_method",
                "is_family_plan",
                "is_loyalty_plan",
                "requires_special_authorization",
            ],
        )
        self.assertEqual(
            [field.name for field in form.pricing_fields],
            [
                "price",
                "monthly_reference_price",
                "base_monthly_net_price",
                "cycle_discount_percentage",
                "teacher_commission_percentage",
            ],
        )
        self.assertEqual(
            [field.name for field in form.gateway_fields],
            [
                "gateway_code",
                "gateway_fixed_fee",
                "gateway_percentage_fee",
            ],
        )
