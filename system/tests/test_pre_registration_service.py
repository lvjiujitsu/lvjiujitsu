from django.test import TestCase

from system.models import (
    BeltRank,
    CategoryAudience,
    Person,
    PreRegistration,
    PreRegistrationStatus,
)
from system.services.pre_registration import (
    finalize_pre_registration,
    mark_pre_registration_trial_requested,
)
from system.services.registration_checkout import create_pre_registration_plan_payment


class FinalizePreRegistrationServiceTestCase(TestCase):
    def setUp(self):
        BeltRank.objects.get_or_create(
            code="adult-white",
            defaults={
                "display_name": "Branca Adulto",
                "audience": CategoryAudience.ADULT,
                "display_order": 1,
                "is_active": True,
            },
        )

    def _build_pre_registration(self, cpf="390.533.447-05"):
        return PreRegistration.objects.create(
            session_key="test-session",
            registration_profile="holder",
            holder_cpf=cpf,
            holder_email="final@example.com",
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "registration_profile": "holder",
                "holder_name": "Aluno Final",
                "holder_cpf": cpf,
                "holder_birthdate": "10/10/1990",
                "holder_biological_sex": "male",
                "holder_email": "final@example.com",
                "holder_password": "Teste@12345",
                "holder_password_confirm": "Teste@12345",
                "holder_has_martial_art": "no",
                "checkout_action": "asaas_card",
            },
        )

    def test_finalize_creates_person_and_marks_pre_registration_finalized(self):
        pre_registration = self._build_pre_registration()

        result = finalize_pre_registration(pre_registration)

        self.assertTrue(result["ok"])
        self.assertFalse(result["already_finalized"])
        self.assertIsNotNone(result["person"])
        self.assertTrue(Person.objects.filter(cpf="390.533.447-05").exists())
        pre_registration.refresh_from_db()
        self.assertEqual(pre_registration.status, PreRegistrationStatus.FINALIZED)
        self.assertEqual(pre_registration.finalized_person, result["person"])

    def test_finalize_is_idempotent_when_already_finalized(self):
        pre_registration = self._build_pre_registration()
        first_result = finalize_pre_registration(pre_registration)
        self.assertTrue(first_result["ok"])

        pre_registration.refresh_from_db()
        second_result = finalize_pre_registration(pre_registration)

        self.assertTrue(second_result["ok"])
        self.assertTrue(second_result["already_finalized"])
        self.assertEqual(Person.objects.filter(cpf="390.533.447-05").count(), 1)

    def test_finalize_guardian_without_own_birthdate_does_not_crash(self):
        BeltRank.objects.get_or_create(
            code="kids-white",
            defaults={
                "display_name": "Branca Infantil",
                "audience": CategoryAudience.KIDS,
                "min_age": 4,
                "max_age": 15,
                "display_order": 1,
                "is_active": True,
            },
        )
        pre_registration = PreRegistration.objects.create(
            session_key="test-session-guardian",
            registration_profile="guardian",
            holder_email="guardian@example.com",
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "registration_profile": "guardian",
                "guardian_name": "Responsavel Sem Nascimento",
                "guardian_cpf": "533.976.299-85",
                "guardian_biological_sex": "female",
                "guardian_password": "Teste@12345",
                "guardian_password_confirm": "Teste@12345",
                "guardian_has_martial_art": "no",
                "student_name": "Dependente Do Responsavel",
                "student_cpf": "084.598.961-88",
                "student_birthdate": "15/03/2015",
                "student_biological_sex": "male",
                "student_password": "Teste@12345",
                "student_password_confirm": "Teste@12345",
                "student_kinship_type": "mother",
                "student_class_groups": [],
                "extra_dependents": [],
                "checkout_action": "asaas_card",
            },
        )

        result = finalize_pre_registration(pre_registration)

        self.assertTrue(result["ok"])
        guardian = Person.objects.get(cpf="533.976.299-85")
        dependent = Person.objects.get(cpf="084.598.961-88")
        self.assertIsNone(guardian.birth_date)
        self.assertTrue(dependent.is_active)
        self.assertTrue(dependent.access_account.is_active)

    def test_finalize_returns_error_without_creating_person_on_invalid_snapshot(self):
        pre_registration = PreRegistration.objects.create(
            session_key="test-session-invalid",
            registration_profile="holder",
            holder_cpf="111.111.111-11",
            holder_email="invalid@example.com",
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "registration_profile": "holder",
                "holder_cpf": "111.111.111-11",
            },
        )

        result = finalize_pre_registration(pre_registration)

        self.assertFalse(result["ok"])
        self.assertIsNotNone(result["error"])
        self.assertFalse(Person.objects.filter(cpf="111.111.111-11").exists())
        pre_registration.refresh_from_db()
        self.assertNotEqual(pre_registration.status, PreRegistrationStatus.FINALIZED)


class MarkPreRegistrationTrialRequestedTestCase(TestCase):
    def test_marks_trial_requested_flag_in_snapshot(self):
        pre_registration = PreRegistration.objects.create(
            session_key="trial-session",
            registration_profile="holder",
            holder_cpf="222.222.222-22",
            holder_email="trial@example.com",
            form_snapshot={"registration_profile": "holder"},
        )

        mark_pre_registration_trial_requested(pre_registration)

        pre_registration.refresh_from_db()
        self.assertTrue(pre_registration.form_snapshot.get("trial_requested"))


class CreatePreRegistrationPlanPaymentServiceTestCase(TestCase):
    def test_raises_value_error_without_selected_plan(self):
        pre_registration = PreRegistration.objects.create(
            session_key="plan-session",
            registration_profile="holder",
            holder_cpf="333.333.333-33",
            holder_email="plan@example.com",
            form_snapshot={"registration_profile": "holder"},
        )

        with self.assertRaises(ValueError):
            create_pre_registration_plan_payment(pre_registration, "pix")
