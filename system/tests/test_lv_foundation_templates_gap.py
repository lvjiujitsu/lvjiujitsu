from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import PersonType
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationTemplatesGapTestCase(TestCase):
    """PRD-078: rotas ativas sem template foram resolvidas (exceto loja/backorder, documentado como pendencia)."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-templates-gap",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self._login_technical_admin()

    def test_password_reset_form_renders(self):
        response = self.client.get(reverse("system:password-reset"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_done_renders(self):
        response = self.client.get(reverse("system:password-reset-done"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_complete_renders(self):
        response = self.client.get(reverse("system:password-reset-complete"))
        self.assertEqual(response.status_code, 200)

    def test_admin_hub_renders_with_module_cards(self):
        response = self.client.get(reverse("system:admin-hub"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pessoas")
        self.assertContains(response, "Turmas")

    def test_english_admin_hub_route(self):
        response = self.client.get(reverse("system:admin-hub"))
        self.assertEqual(response.request["PATH_INFO"], "/administration/")

    def test_old_portuguese_admin_hub_redirects(self):
        response = self.client.get("/administracao/")
        self.assertRedirects(response, reverse("system:admin-hub"))

    def test_person_type_list_renders(self):
        PersonType.objects.create(code="test-profile", display_name="Perfil Teste")
        response = self.client.get(reverse("system:person-type-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Perfil Teste")

    def test_create_person_type_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:person-type-create") + "?modal=1",
            data={
                "code": "new-profile",
                "display_name": "Novo Perfil",
                "description": "",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(PersonType.objects.filter(code="new-profile").exists())

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
