import json

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from system.forms import PortalRegistrationForm
from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassGroup,
    Person,
    PersonType,
    PortalAccount,
    PortalPasswordResetToken,
)
from system.services.registration import create_portal_registration


User = get_user_model()


class PersonModelTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_person_has_single_type(self):
        student_type = PersonType.objects.create(
            code="student-test",
            display_name="Aluno teste",
        )
        person = Person.objects.create(
            full_name="Maria Souza",
            cpf="529.982.247-25",
            person_type=student_type,
        )

        self.assertEqual(person.person_type, student_type)
        self.assertTrue(person.has_type_code("student-test"))
        self.assertEqual(str(person), "Maria Souza")

    def test_portal_account_is_independent_from_django_user(self):
        person = Person.objects.create(
            full_name="Carlos Silva",
            cpf="960.013.389-14",
        )
        access_account = PortalAccount(person=person)
        access_account.set_password("SenhaForte@123")
        access_account.save()

        self.assertTrue(access_account.check_password("SenhaForte@123"))
        self.assertEqual(User.objects.count(), 0)

    def test_registration_form_requires_matching_password_confirmation(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Carlos Titular",
                "holder_cpf": "12345678901",
                "holder_birthdate": "01/01/1990",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "654321",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("holder_password_confirm", form.errors)

    def test_password_reset_token_defaults_to_active_window(self):
        person = Person.objects.create(
            full_name="Carlos Silva",
            cpf="104.332.181-00",
            email="carlos@example.com",
        )
        access_account = PortalAccount(person=person)
        access_account.set_password("123456")
        access_account.save()

        reset_token = PortalPasswordResetToken.objects.create(access_account=access_account)

        self.assertTrue(reset_token.is_valid())
        self.assertGreater(reset_token.expires_at, timezone.now())

    def test_other_registration_creates_single_selected_type(self):
        PersonType.objects.create(code="instructor", display_name="Professor")
        form = PortalRegistrationForm(
            data={
                "registration_profile": "other",
                "other_type_code": "instructor",
                "other_name": "Professor Teste",
                "other_cpf": "10433218100",
                "other_birthdate": "01/01/1990",
                "other_biological_sex": "male",
                "other_password": "123456",
                "other_password_confirm": "123456",
                "teacher_assignment_mode": "propose",
                "teacher_proposed_schedule_payload": json.dumps(
                    {
                        "category_id": "1",
                        "display_name": "Adulto Manha",
                        "weekdays": ["monday"],
                        "start_time": "07:00",
                    }
                ),
                "operational_financial_arrangement": "volunteer",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = create_portal_registration(form.cleaned_data)

        self.assertEqual(created["other"].person_type.code, "instructor")

    def test_form_save_raises_not_implemented(self):
        PersonType.objects.create(code="instructor", display_name="Professor")
        form = PortalRegistrationForm(
            data={
                "registration_profile": "other",
                "other_type_code": "instructor",
                "other_name": "Professor Teste",
                "other_cpf": "10433218100",
                "other_birthdate": "01/01/1990",
                "other_biological_sex": "male",
                "other_password": "123456",
                "other_password_confirm": "123456",
                "teacher_assignment_mode": "propose",
                "teacher_proposed_schedule_payload": json.dumps(
                    {
                        "category_id": "1",
                        "display_name": "Adulto Manha",
                        "weekdays": ["monday"],
                        "start_time": "07:00",
                    }
                ),
                "operational_financial_arrangement": "volunteer",
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        with self.assertRaises(NotImplementedError):
            form.save()

    def test_teacher_operational_registration_requires_schedule_weekdays(self):
        PersonType.objects.create(code=PersonTypeCode.INSTRUCTOR, display_name="Professor")
        form = PortalRegistrationForm(
            data={
                **self._base_other_registration_payload(PersonTypeCode.INSTRUCTOR),
                "teacher_assignment_mode": "propose",
                "teacher_proposed_schedule_payload": json.dumps(
                    {
                        "category_id": "1",
                        "display_name": "Adulto Manha",
                        "weekdays": [],
                        "start_time": "07:00",
                    }
                ),
                "operational_financial_arrangement": "volunteer",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("teacher_proposed_schedule_payload", form.errors)

    def test_teacher_operational_registration_accepts_multi_day_schedule_and_paid_pix(self):
        PersonType.objects.create(code=PersonTypeCode.INSTRUCTOR, display_name="Professor")
        form = PortalRegistrationForm(
            data={
                **self._base_other_registration_payload(PersonTypeCode.INSTRUCTOR),
                "teacher_assignment_mode": "propose",
                "teacher_proposed_schedule_payload": json.dumps(
                    {
                        "category_id": "1",
                        "display_name": "Adulto Manha",
                        "weekdays": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "07:00",
                    }
                ),
                "operational_financial_arrangement": "paid_mixed",
                "operational_payout_method": "pix",
                "operational_pix_key_type": "cpf",
                "operational_pix_key": "104.332.181-00",
                "operational_fixed_amount": "300.00",
                "operational_student_percentage": "20",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_teacher_operational_registration_accepts_active_class_with_current_teacher_payload(self):
        instructor_type = PersonType.objects.create(
            code=PersonTypeCode.INSTRUCTOR,
            display_name="Professor",
        )
        current_teacher = Person.objects.create(
            full_name="Professor Atual",
            cpf="136.246.880-02",
            person_type=instructor_type,
        )
        category = ClassCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
        )
        class_group = ClassGroup.objects.create(
            display_name="Adulto Noite",
            class_category=category,
            main_teacher=current_teacher,
        )
        form = PortalRegistrationForm(
            data={
                **self._base_other_registration_payload(PersonTypeCode.INSTRUCTOR),
                "teacher_assignment_mode": "existing",
                "teacher_existing_class_groups_payload": json.dumps(
                    [
                        {
                            "id": class_group.pk,
                            "label": "Adulto · Adulto Noite",
                            "teacher_names": ["Professor Atual"],
                            "approval_scope": "admin_and_current_teacher",
                        }
                    ]
                ),
                "operational_financial_arrangement": "volunteer",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["teacher_existing_class_group"], str(class_group.pk))

    def test_paid_operational_registration_requires_payout_target(self):
        PersonType.objects.create(code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT, display_name="Administrativo")
        form = PortalRegistrationForm(
            data={
                **self._base_other_registration_payload(PersonTypeCode.ADMINISTRATIVE_ASSISTANT),
                "operational_requested_roles_payload": json.dumps(["people-support"]),
                "operational_financial_arrangement": "paid_fixed",
                "operational_payout_method": "none",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("operational_payout_method", form.errors)

    def test_barter_operational_registration_clears_payout_fields(self):
        PersonType.objects.create(code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT, display_name="Administrativo")
        form = PortalRegistrationForm(
            data={
                **self._base_other_registration_payload(PersonTypeCode.ADMINISTRATIVE_ASSISTANT),
                "operational_requested_roles_payload": json.dumps(["people-support"]),
                "operational_financial_arrangement": "barter",
                "operational_payout_method": "pix",
                "operational_pix_key_type": "cpf",
                "operational_pix_key": "104.332.181-00",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["operational_payout_method"], "none")
        self.assertEqual(form.cleaned_data["operational_pix_key"], "")

    def test_administrative_operational_registration_requires_requested_role(self):
        PersonType.objects.create(code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT, display_name="Administrativo")
        form = PortalRegistrationForm(
            data={
                **self._base_other_registration_payload(PersonTypeCode.ADMINISTRATIVE_ASSISTANT),
                "operational_requested_roles_payload": "[]",
                "operational_financial_arrangement": "volunteer",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("operational_requested_roles_payload", form.errors)

    def _base_other_registration_payload(self, person_type_code):
        return {
            "registration_profile": "other",
            "other_type_code": person_type_code,
            "other_name": "Cadastro Operacional",
            "other_cpf": "10433218100",
            "other_birthdate": "01/01/1990",
            "other_biological_sex": BiologicalSex.MALE,
            "other_password": "123456",
            "other_password_confirm": "123456",
        }
