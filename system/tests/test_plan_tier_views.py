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
    PlanPrice,
    PlanTier,
    PlanWeeklyFrequency,
)
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class PlanTierAdministrativeViewsTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-tiers",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-view-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
            display_order=10,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()

    def test_unauthenticated_tier_list_redirects_to_login(self):
        response = self.client.get(reverse("system:plan-tier-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("system:login"), response["Location"])

    def test_technical_admin_can_access_tier_list(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:plan-tier-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tier.display_name)
        self.assertContains(response, "Novo tier")

    def test_tier_detail_shows_nested_prices_and_usage(self):
        self._login_technical_admin()

        response = self.client.get(
            reverse("system:plan-tier-detail", kwargs={"pk": self.tier.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tier.display_name)
        self.assertContains(response, "stripe_card")
        self.assertContains(response, "Uso do tier")

    def test_tier_create_persists_new_tier(self):
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:plan-tier-create"),
            {
                "code": "kids-5x-view-test",
                "display_name": "Kids 5x por semana",
                "audience": PlanAudience.KIDS_JUVENILE,
                "weekly_frequency": PlanWeeklyFrequency.FIVE_TIMES,
                "family_discount_percentage": "0.18",
                "display_order": "0",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(PlanTier.objects.filter(code="kids-5x-view-test").exists())

    def test_tier_delete_protected_by_price_redirects_with_explicit_message(self):
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:plan-tier-delete", kwargs={"pk": self.tier.pk})
        )

        self.assertRedirects(
            response,
            reverse("system:plan-tier-detail", kwargs={"pk": self.tier.pk}),
        )
        self.assertTrue(PlanTier.objects.filter(pk=self.tier.pk).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn(
            "Este tier não pode ser excluído porque possui preços cadastrados.",
            messages,
        )


class PlanPriceAdministrativeViewsTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-precos",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-price-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()

    def test_price_create_persists_new_price_under_tier(self):
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:plan-price-create", kwargs={"tier_pk": self.tier.pk}),
            {
                "payment_method": PlanPaymentMethod.PIX,
                "billing_cycle": BillingCycle.MONTHLY,
                "gateway_code": "asaas_pix",
                "base_monthly_net_price": "200.00",
                "cycle_discount_percentage": "0",
                "gateway_fixed_fee": "0",
                "gateway_percentage_fee": "0",
                "teacher_commission_percentage": "0",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PlanPrice.objects.filter(tier=self.tier, gateway_code="asaas_pix").exists()
        )

    def test_price_update_form_disables_pricing_fields_when_referenced(self):
        person = Person.objects.create(
            full_name="Aluno com preco",
            cpf="123.456.789-10",
        )
        Membership.objects.create(
            person=person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
        )
        self._login_technical_admin()

        response = self.client.get(
            reverse("system:plan-price-update", kwargs={"pk": self.price.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "somente leitura")

    def test_price_update_rejects_pricing_change_when_referenced(self):
        person = Person.objects.create(
            full_name="Aluno com preco protegido",
            cpf="987.654.321-00",
        )
        Membership.objects.create(
            person=person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
        )
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:plan-price-update", kwargs={"pk": self.price.pk}),
            {
                "payment_method": PlanPaymentMethod.CREDIT_CARD,
                "billing_cycle": BillingCycle.MONTHLY,
                "gateway_code": "stripe_card",
                "base_monthly_net_price": "999.00",
                "cycle_discount_percentage": "0",
                "gateway_fixed_fee": "0",
                "gateway_percentage_fee": "0",
                "teacher_commission_percentage": "0",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.price.refresh_from_db()
        self.assertEqual(self.price.base_monthly_net_price, Decimal("200.00"))

    def test_price_delete_protected_by_membership_redirects_with_explicit_message(self):
        person = Person.objects.create(
            full_name="Aluno com preco vinculado",
            cpf="111.222.333-44",
        )
        Membership.objects.create(
            person=person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
        )
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:plan-price-delete", kwargs={"pk": self.price.pk})
        )

        self.assertRedirects(
            response,
            reverse("system:plan-tier-detail", kwargs={"pk": self.tier.pk}),
        )
        self.assertTrue(PlanPrice.objects.filter(pk=self.price.pk).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(
            any("não pode ser excluído" in message for message in messages)
        )
