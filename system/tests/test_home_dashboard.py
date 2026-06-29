from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import Person, PersonType
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class HomeDashboardContractTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-home",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        student_type = PersonType.objects.create(code="student", display_name="Aluno")
        Person.objects.create(
            full_name="Aluno Visual",
            cpf="111.111.111-11",
            person_type=student_type,
            jiu_jitsu_belt="white",
            jiu_jitsu_stripes=4,
        )

    def test_home_is_minimal_people_first_surface(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Acesso rápido", content)
        self.assertIn("Pessoas", content)
        self.assertIn(f'href="{reverse("system:person-list")}"', content)
        self.assertIn('href="/admin/"', content)
        self.assertIn("Aluno Visual", content)
        self.assertIn("person-belt", content)
        self.assertNotIn("Planos", content)
        self.assertNotIn("Turmas", content)
        self.assertNotIn("Financeiro", content)
        self.assertNotIn("quick-link--disabled", content)
        self.assertNotIn('href="#"', content)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
