from datetime import date

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import Person, PersonType, PortalAccount
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.password_reset import (
    find_resettable_account,
    make_reset_credentials,
)
from system.services.portal_auth import DEFAULT_TEMP_PASSWORD


class PasswordChangeTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Aluno Troca Senha",
            cpf="223.365.480-38",
            person_type=self.student_type,
            birth_date=date(1995, 1, 1),
            email="aluno.senha.teste@lvjiujitsu.test",
        )
        self.account = PortalAccount.objects.create(person=self.person)
        self.account.set_password("SenhaAntiga@1")
        self.account.save(update_fields=["password_hash", "password_updated_at"])

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_forgot_password_sends_a_link_and_keeps_the_current_password(self):
        response = self.client.post(
            reverse("system:password-reset"),
            data={"cpf": self.person.cpf},
        )
        self.assertRedirects(response, reverse("system:password-reset-sent"))
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("SenhaAntiga@1"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/password-reset/", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.person.email])

    def test_forgot_password_keeps_quiet_about_an_unknown_cpf(self):
        response = self.client.post(
            reverse("system:password-reset"),
            data={"cpf": "390.533.447-05"},
        )
        self.assertRedirects(response, reverse("system:password-reset-sent"))
        self.assertEqual(mail.outbox, [])

    def test_the_reset_link_changes_the_password(self):
        kind, account = find_resettable_account(self.person.cpf)
        identifier, token = make_reset_credentials(kind, account)
        form_response = self.client.get(
            reverse("system:password-reset-confirm", args=[identifier, token]),
            follow=True,
        )

        response = self.client.post(
            form_response.request["PATH_INFO"],
            data={"new_password1": "SenhaNova@2", "new_password2": "SenhaNova@2"},
        )

        self.assertRedirects(response, reverse("system:password-reset-done"))
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("SenhaNova@2"))

    def test_the_reset_link_stops_working_after_it_is_used(self):
        kind, account = find_resettable_account(self.person.cpf)
        identifier, token = make_reset_credentials(kind, account)
        link = reverse("system:password-reset-confirm", args=[identifier, token])
        form_response = self.client.get(link, follow=True)
        self.client.post(
            form_response.request["PATH_INFO"],
            data={"new_password1": "SenhaNova@2", "new_password2": "SenhaNova@2"},
        )

        replayed = self.client.get(link, follow=True)

        self.assertContains(replayed, "Link inválido")

    def test_login_with_default_password_redirects_to_forced_change(self):
        self.account.set_password(DEFAULT_TEMP_PASSWORD)
        self.account.save(update_fields=["password_hash", "password_updated_at"])

        response = self.client.post(
            reverse("system:login"),
            data={"identifier": self.person.cpf, "password": DEFAULT_TEMP_PASSWORD},
        )
        self.assertRedirects(response, reverse("system:password-change"))
        self.assertNotIn(PORTAL_ACCOUNT_SESSION_KEY, self.client.session)
        self.assertEqual(
            self.client.session.get("forced_password_change_account_id"),
            self.account.pk,
        )

    def test_forced_password_change_requires_default_as_old_password(self):
        self.account.set_password(DEFAULT_TEMP_PASSWORD)
        self.account.save(update_fields=["password_hash", "password_updated_at"])
        session = self.client.session
        session["forced_password_change_account_id"] = self.account.pk
        session.save()

        response = self.client.post(
            reverse("system:password-change"),
            data={
                "old_password": "senha-errada",
                "new_password1": "SenhaNova@2",
                "new_password2": "SenhaNova@2",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password(DEFAULT_TEMP_PASSWORD))

    def test_forced_password_change_completes_and_logs_in(self):
        self.account.set_password(DEFAULT_TEMP_PASSWORD)
        self.account.save(update_fields=["password_hash", "password_updated_at"])
        session = self.client.session
        session["forced_password_change_account_id"] = self.account.pk
        session.save()

        response = self.client.post(
            reverse("system:password-change"),
            data={
                "old_password": DEFAULT_TEMP_PASSWORD,
                "new_password1": "SenhaNova@2",
                "new_password2": "SenhaNova@2",
            },
        )
        self.assertRedirects(
            response, reverse("system:dashboard-redirect"), target_status_code=302
        )
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("SenhaNova@2"))
        self.assertEqual(
            self.client.session.get(PORTAL_ACCOUNT_SESSION_KEY), self.account.pk
        )
        self.assertNotIn("forced_password_change_account_id", self.client.session)

    def test_voluntary_password_change_requires_login(self):
        response = self.client.get(reverse("system:password-change"))
        self.assertRedirects(response, reverse("system:login"))

    def test_voluntary_password_change_requires_correct_old_password(self):
        self._login()
        response = self.client.post(
            reverse("system:password-change"),
            data={
                "old_password": "senha-errada",
                "new_password1": "SenhaNova@2",
                "new_password2": "SenhaNova@2",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("SenhaAntiga@1"))

    def test_voluntary_password_change_rejects_mismatched_new_passwords(self):
        self._login()
        response = self.client.post(
            reverse("system:password-change"),
            data={
                "old_password": "SenhaAntiga@1",
                "new_password1": "SenhaNova@2",
                "new_password2": "SenhaDiferente@3",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("SenhaAntiga@1"))

    def test_voluntary_password_change_success(self):
        self._login()
        response = self.client.post(
            reverse("system:password-change"),
            data={
                "old_password": "SenhaAntiga@1",
                "new_password1": "SenhaNova@2",
                "new_password2": "SenhaNova@2",
            },
        )
        self.assertRedirects(
            response, reverse("system:dashboard-redirect"), target_status_code=302
        )
        self.account.refresh_from_db()
        self.assertTrue(self.account.check_password("SenhaNova@2"))
