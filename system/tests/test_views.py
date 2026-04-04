from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import Person, PersonType


User = get_user_model()


class PortalViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@admin.com",
            password="admin",
        )

    def test_root_route_returns_approved_home_page(self):
        response = self.client.get(reverse("system:root"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Falar com a LV")
        self.assertContains(response, "Cadastro")

    def test_legacy_home_route_returns_approved_home_page(self):
        response = self.client.get(reverse("system:legacy-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Falar com a LV")
        self.assertContains(response, "Cadastro")

    def test_legacy_login_form_route_returns_mobile_login_page(self):
        response = self.client.get(reverse("system:legacy-login-form"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre com seu CPF ou usu")

    def test_legacy_register_route_returns_complete_registration_page(self):
        response = self.client.get(reverse("system:legacy-register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estrutura do cadastro")
        self.assertContains(response, "Incluir dependente")

    def test_admin_user_can_log_in_and_reach_admin_home(self):
        response = self.client.post(
            reverse("system:login"),
            {"username": "admin", "password": "admin"},
            follow=True,
        )

        self.assertRedirects(response, reverse("system:admin-home"))

    def test_staff_user_can_create_person(self):
        self.client.force_login(self.admin_user)
        student_type = PersonType.objects.create(
            code="student-test",
            display_name="Aluno teste",
        )

        response = self.client.post(
            reverse("system:person-create"),
            {
                "full_name": "Carlos Pereira",
                "cpf": "111.222.333-44",
                "email": "carlos@example.com",
                "phone": "(62) 99999-0000",
                "birth_date": "1990-01-01",
                "is_active": "on",
                "person_types": [student_type.pk],
            },
        )

        self.assertRedirects(response, reverse("system:person-list"))
        self.assertTrue(Person.objects.filter(cpf="111.222.333-44").exists())
