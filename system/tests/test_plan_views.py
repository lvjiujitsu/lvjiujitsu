from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import PersonType, Person, PortalAccount
from system.models.plan import BillingCycle, SubscriptionPlan
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY

User = get_user_model()


class PlanViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin",
        )
        self.admin_type = PersonType.objects.create(
            code="administrative-assistant",
            display_name="Auxiliar administrativo",
        )
        self.plan = SubscriptionPlan.objects.create(
            code="mensal-test",
            display_name="Plano Mensal Teste",
            price=Decimal("250.00"),
            billing_cycle=BillingCycle.MONTHLY,
        )
        self.portal_account = self._create_portal_account(
            full_name="Admin Teste",
            cpf="111.111.111-11",
            person_type=self.admin_type,
        )

    def _create_portal_account(self, *, full_name, cpf, person_type):
        person = Person.objects.create(
            full_name=full_name, cpf=cpf, person_type=person_type,
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        return account

    def _login_as_admin(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.portal_account.pk
        session[TECHNICAL_ADMIN_SESSION_KEY] = True
        session.save()

    def test_plan_list_requires_auth(self):
        response = self.client.get(reverse("system:plan-list"))
        self.assertNotEqual(response.status_code, 200)

    def test_plan_list_loads(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:plan-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano Mensal Teste")

    def test_plan_detail_loads(self):
        self._login_as_admin()
        response = self.client.get(
            reverse("system:plan-detail", args=[self.plan.pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mensal-test")

    def test_plan_create_page_loads(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:plan-create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cadastrar plano")

    def test_plan_delete_confirm_loads(self):
        self._login_as_admin()
        response = self.client.get(
            reverse("system:plan-delete", args=[self.plan.pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Excluir plano")

    def test_plan_delete_removes(self):
        self._login_as_admin()
        self.client.post(
            reverse("system:plan-delete", args=[self.plan.pk]),
        )
        self.assertFalse(SubscriptionPlan.objects.filter(pk=self.plan.pk).exists())

    def test_plan_catalog_public_page_loads(self):
        response = self.client.get(reverse("system:plan-catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planos disponíveis")
        self.assertContains(response, "Plano Mensal Teste")

    def test_plan_catalog_hides_inactive(self):
        self.plan.is_active = False
        self.plan.save()
        response = self.client.get(reverse("system:plan-catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Plano Mensal Teste")

    def test_home_page_has_planos_button(self):
        response = self.client.get(reverse("system:legacy-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planos")

    def test_info_page_does_not_show_plans(self):
        response = self.client.get(reverse("system:info"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Plano Mensal Teste")
        self.assertNotContains(response, "Planos disponíveis")

    def test_update_redirects_to_detail(self):
        self._login_as_admin()
        response = self.client.post(
            reverse("system:plan-update", args=[self.plan.pk]),
            {
                "code": "mensal-test",
                "display_name": "Plano Editado",
                "billing_cycle": "monthly",
                "price": "250.00",
                "display_order": "0",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/plans/{self.plan.pk}/", response.url)

    def test_admin_dashboard_shows_planos(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:admin-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planos")

    def test_student_dashboard_shows_planos(self):
        student_type = PersonType.objects.create(code="student", display_name="Aluno")
        student_account = self._create_portal_account(
            full_name="Aluno Teste", cpf="222.222.222-22", person_type=student_type,
        )
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = student_account.pk
        session.save()
        response = self.client.get(reverse("system:student-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planos")
