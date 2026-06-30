from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.services import TECHNICAL_ADMIN_SESSION_KEY


class HomeDashboardContractTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-home",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )

    def test_technical_admin_home_renders_staff_sections(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Acesso rápido", content)
        self.assertIn("Pessoas", content)
        self.assertIn("Turmas", content)
        self.assertIn("Financeiro", content)
        self.assertIn("Graduação", content)
        self.assertIn("Materiais", content)
        self.assertIn("Planos", content)
        self.assertIn("Perfis e acessos", content)
        self.assertIn("Turmas de hoje", content)
        self.assertIn("Disponível", content)
        self.assertIn("A receber", content)
        self.assertIn("Pendências", content)
        self.assertIn(f'href="{reverse("system:person-list")}"', content)
        self.assertNotIn('href="/admin/"', content)
        self.assertNotIn("Django Admin", content)
        self.assertNotIn("quick-link--disabled", content)
        self.assertNotIn('href="#"', content)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
