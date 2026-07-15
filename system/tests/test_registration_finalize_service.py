from django.test import TestCase

from system.models import Person, PreRegistration, PreRegistrationStatus
from system.services.registration_finalize import RegistrationFinalizeService


class RegistrationFinalizeServiceTestCase(TestCase):
    def test_create_from_pre_registration_delegates_to_create_portal_registration(self):
        pre_registration = PreRegistration.objects.create(
            session_key="finalize-service",
            registration_profile="holder",
            holder_cpf="390.533.447-05",
            holder_email="service@example.com",
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "registration_profile": "holder",
                "holder_name": "Aluno Service",
                "holder_cpf": "390.533.447-05",
                "holder_birthdate": "10/10/1990",
                "holder_biological_sex": "male",
                "holder_email": "service@example.com",
                "holder_password": "Teste@12345",
                "holder_password_confirm": "Teste@12345",
                "holder_has_martial_art": "no",
                "checkout_action": "asaas_card",
                "extra_dependents": [
                    {"name": "Dependente", "dependent_password": "Teste@12345"}
                ],
            },
        )

        result = RegistrationFinalizeService.create_from_pre_registration(pre_registration)

        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["person"])
        self.assertTrue(Person.objects.filter(cpf="390.533.447-05").exists())
        pre_registration.refresh_from_db()
        self.assertEqual(pre_registration.status, PreRegistrationStatus.FINALIZED)
        self.assertNotIn("holder_password", pre_registration.form_snapshot)
        self.assertNotIn("holder_password_confirm", pre_registration.form_snapshot)
        self.assertNotIn(
            "dependent_password",
            pre_registration.form_snapshot["extra_dependents"][0],
        )
