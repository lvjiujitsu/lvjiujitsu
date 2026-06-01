from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from system.models import (
    BillingCycle,
    Membership,
    MembershipStatus,
    Person,
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class PlanAdministrativeViewsTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-planos",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.adult_plan = SubscriptionPlan.objects.create(
            code="adult-five-monthly-card",
            display_name="Adulto 5x Mensal Cartão",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            price=Decimal("249.90"),
            display_order=10,
        )
        self.kids_plan = SubscriptionPlan.objects.create(
            code="kids-two-quarterly-pix",
            display_name="Kids 2x Trimestral PIX",
            audience=PlanAudience.KIDS_JUVENILE,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            billing_cycle=BillingCycle.QUARTERLY,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            price=Decimal("499.90"),
            display_order=20,
        )

    def test_unauthenticated_plan_list_redirects_to_login(self):
        response = self.client.get(reverse("system:plan-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("system:login"), response["Location"])

    def test_technical_admin_can_access_plan_list(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:plan-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planos")
        self.assertContains(response, self.adult_plan.display_name)
        self.assertContains(response, self.kids_plan.display_name)
        self.assertContains(response, "Novo plano")

    def test_plan_list_filters_by_gateway(self):
        self._login_technical_admin()

        response = self.client.get(
            reverse("system:plan-list"),
            {"gateway_code": "stripe_card"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.adult_plan.display_name)
        self.assertNotContains(response, self.kids_plan.display_name)
        self.assertEqual(list(response.context["plans"]), [self.adult_plan])

    def test_plan_detail_shows_pricing_gateway_and_usage_context(self):
        self._login_technical_admin()

        response = self.client.get(
            reverse("system:plan-detail", kwargs={"pk": self.adult_plan.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.adult_plan.display_name)
        self.assertContains(response, "Precificação")
        self.assertContains(response, "Gateway")
        self.assertContains(response, "Stripe")
        self.assertContains(response, "Uso do plano")
        self.assertContains(response, "stripe_card")

    def test_plan_create_form_renders_pricing_and_gateway_fields(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:plan-create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Valor líquido mensal desejado")
        self.assertContains(response, 'name="base_monthly_net_price"')
        self.assertContains(response, "Taxa fixa do gateway")
        self.assertContains(response, 'name="gateway_code"')
        self.assertContains(response, "Salvar plano")

    def test_plan_delete_protected_by_membership_redirects_with_explicit_message(self):
        person = Person.objects.create(
            full_name="Aluno com plano",
            cpf="123.456.789-10",
        )
        Membership.objects.create(
            person=person,
            plan=self.adult_plan,
            status=MembershipStatus.ACTIVE,
        )
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:plan-delete", kwargs={"pk": self.adult_plan.pk})
        )

        self.assertRedirects(
            response,
            reverse("system:plan-detail", kwargs={"pk": self.adult_plan.pk}),
        )
        self.assertTrue(SubscriptionPlan.objects.filter(pk=self.adult_plan.pk).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn(
            "Este plano não pode ser excluído porque possui assinaturas vinculadas.",
            messages,
        )

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
