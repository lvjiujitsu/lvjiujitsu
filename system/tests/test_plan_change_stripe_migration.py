"""PRD-132: transição livre entre planos, incluindo migração de gateway
(Asaas -> Stripe recorrente e Stripe -> Asaas) via "Trocar plano"."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
    RegistrationOrder,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.models.registration_order import OrderKind
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.plan_change import build_plan_catalog, plan_requires_stripe_checkout
from system.services.registration_checkout import build_catalog_plan_id, CATALOG_ID_PREFIX_PLAN_PRICE
from system.services.stripe_webhooks import _apply_stripe_plan_change_migration
from system.views.payment_views import _resolve_order_gateway_code


def pp_id(pk):
    return build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, pk)


class PlanChangeCatalogIncludesStripeTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-stripe-catalog-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price_asaas = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.price_stripe = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("210.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Catalogo Stripe", cpf="529.982.247-25",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price_asaas, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10), current_period_end=now + timedelta(days=20),
        )

    def test_catalog_includes_stripe_target_when_not_locked(self):
        catalog = build_plan_catalog(self.person, self.membership)
        by_id = {item["id"]: item for item in catalog}
        self.assertIn(pp_id(self.price_stripe.pk), by_id)
        self.assertTrue(by_id[pp_id(self.price_stripe.pk)]["requires_checkout"])
        self.assertFalse(by_id[pp_id(self.price_asaas.pk)]["requires_checkout"])

    def test_plan_requires_stripe_checkout_helper(self):
        self.assertTrue(plan_requires_stripe_checkout(self.price_stripe))
        self.assertFalse(plan_requires_stripe_checkout(self.price_asaas))


class PlanChangeSelectViewStripeMigrationTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-stripe-select-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price_asaas = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
            stripe_price_id="",
        )
        self.price_stripe = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("210.00"),
            stripe_price_id="price_stripe_migration_test",
        )
        self.person = Person.objects.create(
            full_name="Aluno Migracao Stripe", cpf="960.013.389-14",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE, stripe_customer_id="cus_existing_test",
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    @patch("system.services.stripe_checkout._get_client")
    def test_select_stripe_plan_creates_subscription_order_and_redirects(self, mock_get_client):
        now = timezone.now()
        membership = Membership.objects.create(
            person=self.person, plan_price=self.price_asaas, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10), current_period_end=now + timedelta(days=20),
        )
        mock_client = MagicMock()
        mock_client.checkout.Session.create.return_value = {
            "id": "cs_test_migration", "url": "https://checkout.stripe.com/pay/cs_test_migration",
        }
        mock_get_client.return_value = mock_client

        self._login()
        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": pp_id(self.price_stripe.pk)},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["redirect_url"], "https://checkout.stripe.com/pay/cs_test_migration")

        order = RegistrationOrder.objects.get(person=self.person, is_plan_change=True)
        self.assertEqual(order.plan_price_ref_id, self.price_stripe.pk)
        self.assertEqual(order.kind, OrderKind.SUBSCRIPTION)
        self.assertEqual(order.stripe_session_id, "cs_test_migration")

        membership.refresh_from_db()
        self.assertEqual(membership.plan_price_id, self.price_asaas.pk, "não deve trocar antes da confirmação")

    @patch("system.services.stripe_admin_actions._get_client")
    def test_select_asaas_plan_cancels_existing_stripe_subscription_first(self, mock_get_client):
        now = timezone.now()
        membership = Membership.objects.create(
            person=self.person, plan_price=self.price_stripe, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=40), current_period_end=now - timedelta(days=1),
            stripe_subscription_id="sub_leaving_stripe",
        )
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        self._login()
        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": pp_id(self.price_asaas.pk)},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"], payload)

        mock_client.Subscription.delete.assert_called_once_with("sub_leaving_stripe", prorate=True)

        # Ciclo Stripe já vencido -> sem saldo a aproveitar -> exige novo pagamento
        # (mesmo comportamento de qualquer troca de plano sem crédito disponível),
        # mas a assinatura Stripe antiga já foi cancelada e o status voltou a ativo.
        self.assertIn("redirect_url", payload)
        order = RegistrationOrder.objects.get(person=self.person, is_plan_change=True)
        self.assertEqual(order.plan_price_ref_id, self.price_asaas.pk)

        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.ACTIVE)
        self.assertEqual(membership.stripe_subscription_id, "")


class StripeWebhookPlanChangeMigrationTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-stripe-webhook-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price_asaas = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.price_stripe = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("210.00"),
            stripe_price_id="price_stripe_webhook_test",
        )
        self.person = Person.objects.create(
            full_name="Aluno Webhook Migracao", cpf="153.509.460-56",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price_asaas, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10), current_period_end=now + timedelta(days=20),
        )
        self.order = RegistrationOrder.objects.create(
            person=self.person, plan_price_ref=self.price_stripe, plan_price=self.price_stripe.price,
            total=self.price_stripe.price, kind=OrderKind.SUBSCRIPTION, is_plan_change=True,
        )

    def test_migration_updates_existing_membership_not_creates_new_one(self):
        session = {"subscription": "sub_new_stripe", "customer": "cus_new_stripe"}
        stripe_subscription = {
            "current_period_start": int(timezone.now().timestamp()),
            "current_period_end": int((timezone.now() + timedelta(days=30)).timestamp()),
        }
        result = _apply_stripe_plan_change_migration(
            self.order, session, stripe_subscription=stripe_subscription
        )

        self.assertEqual(result.pk, self.membership.pk)
        self.assertEqual(Membership.objects.filter(person=self.person).count(), 1)

        self.membership.refresh_from_db()
        self.assertEqual(self.membership.plan_price_id, self.price_stripe.pk)
        self.assertEqual(self.membership.stripe_subscription_id, "sub_new_stripe")
        self.assertEqual(self.membership.stripe_customer_id, "cus_new_stripe")
        self.assertIsNotNone(self.membership.current_period_end)

    def test_migration_returns_none_without_active_membership(self):
        self.membership.status = MembershipStatus.CANCELED
        self.membership.save()
        session = {"subscription": "sub_orphan", "customer": "cus_orphan"}
        result = _apply_stripe_plan_change_migration(self.order, session, stripe_subscription=None)
        self.assertIsNone(result)


class PaymentMethodChoiceGatewayResolutionTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-gateway-resolve-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price_asaas_card = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="asaas_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("205.00"),
        )
        self.price_asaas_pix = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.price_stripe = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("210.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Resolve Gateway", cpf="283.958.686-00",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def test_resolves_asaas_card_from_plan_price_ref(self):
        order = RegistrationOrder.objects.create(
            person=self.person, plan_price_ref=self.price_asaas_card,
            plan_price=self.price_asaas_card.price, total=self.price_asaas_card.price,
            is_plan_change=True,
        )
        self.assertEqual(_resolve_order_gateway_code(order), "asaas_card")

    def test_resolves_asaas_pix_from_plan_price_ref(self):
        order = RegistrationOrder.objects.create(
            person=self.person, plan_price_ref=self.price_asaas_pix,
            plan_price=self.price_asaas_pix.price, total=self.price_asaas_pix.price,
            is_plan_change=True,
        )
        self.assertEqual(_resolve_order_gateway_code(order), "asaas_pix")

    def test_resolves_stripe_from_plan_price_ref(self):
        order = RegistrationOrder.objects.create(
            person=self.person, plan_price_ref=self.price_stripe,
            plan_price=self.price_stripe.price, total=self.price_stripe.price,
            is_plan_change=True,
        )
        self.assertEqual(_resolve_order_gateway_code(order), "stripe_card")

    def test_resolves_default_pix_without_plan(self):
        order = RegistrationOrder.objects.create(
            person=self.person, plan_price=Decimal("100.00"), total=Decimal("100.00"),
        )
        self.assertEqual(_resolve_order_gateway_code(order), "asaas_pix")
