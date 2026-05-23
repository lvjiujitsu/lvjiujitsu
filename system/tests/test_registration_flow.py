from django.test import TestCase
from django.urls import reverse

from system.models import (
    BeltRank,
    CategoryAudience,
    Person,
    PreRegistration,
    PreRegistrationStatus,
)


class RegistrationWizardContractTestCase(TestCase):
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

    def test_register_post_creates_pre_registration_without_person(self):
        data = {
            "registration_profile": "holder",
            "holder_name": "Aluno Pre Cadastro",
            "holder_cpf": "529.982.247-25",
            "holder_birthdate": "10/10/1990",
            "holder_biological_sex": "male",
            "holder_email": "aluno.pre@example.com",
            "holder_password": "Teste@12345",
            "holder_password_confirm": "Teste@12345",
            "holder_has_martial_art": "no",
            "checkout_action": "pay_later",
        }

        response = self.client.post(reverse("system:register"), data)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Person.objects.filter(cpf="529.982.247-25").exists())
        pre_registration = PreRegistration.objects.get(holder_cpf="529.982.247-25")
        self.assertEqual(pre_registration.status, PreRegistrationStatus.DRAFT)
        self.assertEqual(pre_registration.form_snapshot["holder_name"], "Aluno Pre Cadastro")

    def test_finalize_creates_person_only_after_explicit_final_step(self):
        pre_registration = PreRegistration.objects.create(
            session_key="test-session",
            registration_profile="holder",
            holder_cpf="390.533.447-05",
            holder_email="final@example.com",
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "registration_profile": "holder",
                "holder_name": "Aluno Final",
                "holder_cpf": "390.533.447-05",
                "holder_birthdate": "10/10/1990",
                "holder_biological_sex": "male",
                "holder_email": "final@example.com",
                "holder_password": "Teste@12345",
                "holder_password_confirm": "Teste@12345",
                "holder_has_martial_art": "no",
                "checkout_action": "asaas_card",
            },
        )
        session = self.client.session
        session["pending_pre_registration_id"] = pre_registration.pk
        session["post_plan_payment_complete"] = True
        session["post_materials_skipped"] = True
        session.save()

        response = self.client.post(reverse("system:register-finalize"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Person.objects.filter(cpf="390.533.447-05").exists())
        pre_registration.refresh_from_db()
        self.assertEqual(pre_registration.status, PreRegistrationStatus.FINALIZED)
