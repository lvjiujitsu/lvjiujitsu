import json

from django.test import TestCase
from django.urls import reverse

from system.constants import OperationalRoleCode, PersonTypeCode
from system.models import (
    AdministrativeAccessRequest,
    AdministrativeAccessRequestStatus,
    BeltRank,
    CategoryAudience,
    ClassCatalogRequest,
    ClassCatalogRequestStatus,
    ClassCategory,
    Person,
    PersonType,
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
        PersonType.objects.get_or_create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            defaults={"display_name": "Administrativo", "is_active": True},
        )
        PersonType.objects.get_or_create(
            code=PersonTypeCode.INSTRUCTOR,
            defaults={"display_name": "Professor", "is_active": True},
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

    def test_administrative_wizard_submission_creates_pending_access_request(self):
        data = {
            "registration_profile": "other",
            "other_type_code": PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            "other_name": "Administrativo Pendente",
            "other_cpf": "71320260896",
            "other_birthdate": "20/08/1990",
            "other_biological_sex": "male",
            "other_email": "admin.pending@example.com",
            "other_phone": "11970000008",
            "other_password": "Teste@12345",
            "other_password_confirm": "Teste@12345",
            "other_has_martial_art": "no",
            "operational_training_intent": "none",
            "operational_requested_roles_payload": json.dumps(
                [OperationalRoleCode.PEOPLE_SUPPORT]
            ),
            "operational_financial_arrangement": "volunteer",
            "checkout_action": "pay_later",
        }

        response = self.client.post(reverse("system:register"), data)

        self.assertRedirects(response, reverse("system:login"))
        self.assertFalse(Person.objects.filter(cpf="713.202.608-96").exists())
        access_request = AdministrativeAccessRequest.objects.get(cpf="713.202.608-96")
        self.assertEqual(access_request.status, AdministrativeAccessRequestStatus.PENDING)
        self.assertEqual(
            access_request.requested_role_codes,
            [OperationalRoleCode.PEOPLE_SUPPORT],
        )
        pre_registration = PreRegistration.objects.get(holder_cpf="713.202.608-96")
        self.assertEqual(pre_registration.status, PreRegistrationStatus.FINALIZED)
        self.assertNotIn("other_password", pre_registration.form_snapshot)
        self.assertNotIn("other_password_confirm", pre_registration.form_snapshot)

    def test_teacher_wizard_submission_creates_pending_class_request(self):
        category = ClassCategory.objects.create(
            code="adult-registration-flow",
            display_name="Adulto Cadastro",
            audience=CategoryAudience.ADULT,
        )
        data = {
            "registration_profile": "other",
            "other_type_code": PersonTypeCode.INSTRUCTOR,
            "other_name": "Professor Pendente",
            "other_cpf": "71320260977",
            "other_birthdate": "21/09/1989",
            "other_biological_sex": "male",
            "other_email": "teacher.pending@example.com",
            "other_phone": "11970000009",
            "other_password": "Teste@12345",
            "other_password_confirm": "Teste@12345",
            "other_has_martial_art": "no",
            "teacher_assignment_mode": "propose",
            "teacher_proposed_schedule_payload": json.dumps(
                {
                    "category_id": str(category.pk),
                    "display_name": "Jiu Jitsu Auditoria",
                    "weekdays": ["monday", "wednesday"],
                    "training_style": "mixed",
                    "start_time": "20:00",
                    "duration_minutes": "60",
                    "default_capacity": "20",
                    "justification": "Proposta enviada pelo cadastro público.",
                }
            ),
            "operational_financial_arrangement": "volunteer",
            "checkout_action": "pay_later",
        }

        response = self.client.post(reverse("system:register"), data)

        self.assertRedirects(response, reverse("system:login"))
        self.assertFalse(Person.objects.filter(cpf="713.202.609-77").exists())
        class_request = ClassCatalogRequest.objects.get(cpf="713.202.609-77")
        self.assertEqual(class_request.status, ClassCatalogRequestStatus.PENDING)
        self.assertEqual(class_request.weekday, "monday")
        self.assertEqual(len(class_request.extra_schedules), 1)
        pre_registration = PreRegistration.objects.get(holder_cpf="713.202.609-77")
        self.assertEqual(pre_registration.status, PreRegistrationStatus.FINALIZED)
        self.assertNotIn("other_password", pre_registration.form_snapshot)
        self.assertNotIn("other_password_confirm", pre_registration.form_snapshot)
