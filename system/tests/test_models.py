from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from system.forms import PortalRegistrationForm
from system.models import (
    BiologicalSex,
    Person,
    PersonType,
    PortalAccount,
    PortalPasswordResetToken,
)
from system.services.portal_auth import create_password_reset_token, reset_portal_password


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

    @patch("system.services.portal_auth.send_mail")
    def test_password_reset_token_request_invalidates_previous_active_tokens(self, mocked_send_mail):
        person = Person.objects.create(
            full_name="Carlos Silva",
            cpf="529.982.247-25",
            email="carlos@example.com",
        )
        access_account = PortalAccount(person=person)
        access_account.set_password("123456")
        access_account.save()
        previous_token = PortalPasswordResetToken.objects.create(access_account=access_account)

        request = self.request_factory.get("/templates/login/esqueci-a-senha.html")
        request.META["HTTP_HOST"] = "testserver"
        create_password_reset_token(person.cpf, request)

        previous_token.refresh_from_db()
        self.assertIsNotNone(previous_token.used_at)
        self.assertEqual(PortalPasswordResetToken.objects.filter(access_account=access_account).count(), 2)
        self.assertEqual(
            PortalPasswordResetToken.objects.filter(
                access_account=access_account,
                used_at__isnull=True,
            ).count(),
            1,
        )
        mocked_send_mail.assert_called_once()

    def test_reset_password_marks_other_open_tokens_as_used(self):
        person = Person.objects.create(
            full_name="Carlos Silva",
            cpf="960.013.389-14",
            email="carlos@example.com",
        )
        access_account = PortalAccount(person=person)
        access_account.set_password("123456")
        access_account.save()

        target_token = PortalPasswordResetToken.objects.create(access_account=access_account)
        extra_token = PortalPasswordResetToken.objects.create(access_account=access_account)

        reset_portal_password(target_token, "NovaSenha@123")

        target_token.refresh_from_db()
        extra_token.refresh_from_db()
        access_account.refresh_from_db()

        self.assertIsNotNone(target_token.used_at)
        self.assertIsNotNone(extra_token.used_at)
        self.assertTrue(access_account.check_password("NovaSenha@123"))

    def test_other_registration_creates_single_selected_type(self):
        PersonType.objects.create(code="instructor", display_name="Professor")
        form = PortalRegistrationForm(
            data={
                "registration_profile": "other",
                "other_type_code": "instructor",
                "other_name": "Professor Teste",
                "other_cpf": "10433218100",
                "other_birthdate": "01/01/1990",
                "other_password": "123456",
                "other_password_confirm": "123456",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        self.assertEqual(created["other"].person_type.code, "instructor")
