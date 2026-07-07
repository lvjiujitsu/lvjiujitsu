from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Membership, MembershipStatus, Person, PersonType
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanTier, PlanPrice, PlanWeeklyFrequency
from system.models.registration_order import PaymentProvider, PaymentStatus, RegistrationOrder
from system.services.asaas_billing_cycle import (
    find_due_asaas_memberships,
    generate_due_asaas_charge,
    generate_due_asaas_charges,
)


def _make_person(name, cpf):
    person_type = PersonType.objects.filter(code=PersonTypeCode.STUDENT).first()
    if person_type is None:
        person_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
    return Person.objects.create(
        full_name=name, cpf=cpf, person_type=person_type,
        birth_date=date(1990, 1, 1), biological_sex=BiologicalSex.MALE,
    )


@override_settings(
    ASAAS_API_KEY="test-key",
    ASAAS_WEBHOOK_TOKEN="wh-token",
    ASAAS_API_URL="https://sandbox.asaas.com/api/v3",
    ASAAS_PIX_EXPIRATION_MINUTES=30,
)
class FindDueAsaasMembershipsTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-billing-cycle",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.pix_price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.card_price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="asaas_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.stripe_price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )

    def _membership(self, person, price, *, period_end, status=MembershipStatus.ACTIVE):
        now = timezone.now()
        return Membership.objects.create(
            person=person, plan_price=price, status=status,
            current_period_start=now, current_period_end=period_end,
        )

    def test_includes_asaas_membership_due_within_lead_days(self):
        person = _make_person("Asaas Vencendo", "390.533.447-05")
        self._membership(person, self.pix_price, period_end=timezone.now() + timedelta(days=2))

        due = find_due_asaas_memberships(lead_days=3)

        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].person, person)

    def test_excludes_membership_not_yet_due(self):
        person = _make_person("Asaas Nao Vencendo", "153.509.460-56")
        self._membership(person, self.pix_price, period_end=timezone.now() + timedelta(days=30))

        due = find_due_asaas_memberships(lead_days=3)

        self.assertEqual(due, [])

    def test_excludes_stripe_membership(self):
        person = _make_person("Stripe Vencendo", "920.000.011-81")
        self._membership(person, self.stripe_price, period_end=timezone.now() + timedelta(days=2))

        due = find_due_asaas_memberships(lead_days=3)

        self.assertEqual(due, [])

    def test_excludes_canceled_membership(self):
        person = _make_person("Asaas Cancelado", "283.958.686-00")
        self._membership(
            person, self.pix_price,
            period_end=timezone.now() + timedelta(days=2),
            status=MembershipStatus.CANCELED,
        )

        due = find_due_asaas_memberships(lead_days=3)

        self.assertEqual(due, [])

    def test_excludes_membership_with_pending_renewal_order(self):
        person = _make_person("Asaas Com Pedido Pendente", "845.669.360-05")
        membership = self._membership(person, self.pix_price, period_end=timezone.now() + timedelta(days=2))
        RegistrationOrder.objects.create(
            person=person, plan_price_ref=self.pix_price, total=Decimal("200.00"),
            payment_status=PaymentStatus.PENDING, payment_provider=PaymentProvider.ASAAS,
        )

        due = find_due_asaas_memberships(lead_days=3)

        self.assertEqual(due, [])


@override_settings(
    ASAAS_API_KEY="test-key",
    ASAAS_WEBHOOK_TOKEN="wh-token",
    ASAAS_API_URL="https://sandbox.asaas.com/api/v3",
    ASAAS_PIX_EXPIRATION_MINUTES=30,
)
class GenerateDueAsaasChargeTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-billing-cycle-charge",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.pix_price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.card_price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="asaas_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )

    @patch("system.services.asaas_checkout.asaas_client.get_pix_qrcode")
    @patch("system.services.asaas_checkout.asaas_client.create_pix_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_uses_billed_price_when_discount_applied(self, m_customer, m_payment, m_qr):
        m_customer.return_value = {"id": "cus_billing_cycle_1"}
        m_payment.return_value = {"id": "pay_billing_cycle_1"}
        m_qr.return_value = {"payload": "copy-paste", "encodedImage": "img"}

        person = _make_person("Asaas Desconto Aplicado", "706.393.640-58")
        now = timezone.now()
        membership = Membership.objects.create(
            person=person, plan_price=self.pix_price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=2),
            family_discount_applied=True, billed_price=Decimal("164.00"),
        )

        order = generate_due_asaas_charge(membership)

        self.assertEqual(order.total, Decimal("164.00"))
        self.assertEqual(order.asaas_payment_id, "pay_billing_cycle_1")

    @patch("system.services.asaas_checkout.asaas_client.create_credit_card_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_uses_full_price_without_discount_and_calls_card_gateway(self, m_customer, m_payment):
        m_customer.return_value = {"id": "cus_billing_cycle_2"}
        m_payment.return_value = {"id": "pay_billing_cycle_2", "invoiceUrl": "https://asaas.test/pay"}

        person = _make_person("Asaas Sem Desconto Cartao", "017.928.500-08")
        now = timezone.now()
        membership = Membership.objects.create(
            person=person, plan_price=self.card_price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=2),
            family_discount_applied=False,
        )

        order = generate_due_asaas_charge(membership)

        self.assertEqual(order.total, Decimal("200.00"))
        m_payment.assert_called_once()

    @patch("system.services.asaas_checkout.asaas_client.get_pix_qrcode")
    @patch("system.services.asaas_checkout.asaas_client.create_pix_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_command_is_idempotent_across_runs(self, m_customer, m_payment, m_qr):
        m_customer.return_value = {"id": "cus_billing_cycle_3"}
        m_payment.return_value = {"id": "pay_billing_cycle_3"}
        m_qr.return_value = {"payload": "copy-paste", "encodedImage": "img"}

        person = _make_person("Asaas Idempotencia", "552.766.030-09")
        now = timezone.now()
        Membership.objects.create(
            person=person, plan_price=self.pix_price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=2),
        )

        first = generate_due_asaas_charges(lead_days=3)
        second = generate_due_asaas_charges(lead_days=3)

        self.assertEqual(len(first["generated"]), 1)
        self.assertEqual(len(second["generated"]), 0)
        self.assertEqual(RegistrationOrder.objects.count(), 1)

    @patch("system.services.asaas_checkout.asaas_client.get_pix_qrcode")
    @patch("system.services.asaas_checkout.asaas_client.create_pix_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_management_command_runs(self, m_customer, m_payment, m_qr):
        m_customer.return_value = {"id": "cus_billing_cycle_4"}
        m_payment.return_value = {"id": "pay_billing_cycle_4"}
        m_qr.return_value = {"payload": "copy-paste", "encodedImage": "img"}

        person = _make_person("Asaas Command", "845.263.870-38")
        now = timezone.now()
        Membership.objects.create(
            person=person, plan_price=self.pix_price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=2),
        )

        out = StringIO()
        call_command("generate_due_asaas_charges", stdout=out)
        self.assertIn("1 cobrança(s) gerada(s)", out.getvalue())
