from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db.utils import OperationalError
from django.test import TestCase, override_settings
from django.utils import timezone

from system.models import (
    DepositStatus,
    Membership,
    MembershipStatus,
    PaymentProvider,
    PayoutKind,
    PayoutStatus,
    Person,
    PersonType,
    PixKeyType,
    PlanPrice,
    PlanTier,
    RegistrationOrder,
    SubscriptionPlan,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.models.registration_order import PaymentStatus
from system.services import asaas_checkout, asaas_client, asaas_payroll, asaas_webhooks
from system.services.asaas_client import AsaasClientError


def _make_person(**kwargs):
    type_code = kwargs.pop("type_code", "student")
    ptype, _ = PersonType.objects.get_or_create(
        code=type_code,
        defaults={"display_name": type_code.replace("-", " ").title()},
    )
    defaults = {
        "full_name": "Fulano Teste",
        "cpf": "12345678901",
        "email": "fulano@example.com",
        "phone": "(62) 99999-9999",
        "birth_date": date(1990, 1, 1),
        "person_type": ptype,
    }
    defaults.update(kwargs)
    return Person.objects.create(**defaults)


@override_settings(
    ASAAS_API_KEY="test-key",
    ASAAS_WEBHOOK_TOKEN="wh-token",
    ASAAS_API_URL="https://sandbox.asaas.com/api/v3",
    ASAAS_PIX_EXPIRATION_MINUTES=30,
)
class AsaasCheckoutTests(TestCase):
    def setUp(self):
        self.person = _make_person()
        self.plan = SubscriptionPlan.objects.create(
            code="mensal",
            display_name="Mensal",
            price=Decimal("150.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        self.order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("150.00"),
            total=Decimal("150.00"),
        )

    @patch("system.services.asaas_checkout.asaas_client.get_pix_qrcode")
    @patch("system.services.asaas_checkout.asaas_client.create_pix_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_create_pix_charge_happy_path(self, m_customer, m_payment, m_qr):
        m_customer.return_value = {"id": "cus_123"}
        m_payment.return_value = {"id": "pay_abc"}
        m_qr.return_value = {
            "payload": "00020101021226...",
            "encodedImage": "base64img",
        }

        pix = asaas_checkout.create_pix_charge_for_order(self.order)

        self.assertEqual(pix["payment_id"], "pay_abc")
        self.assertEqual(pix["copy_paste"], "00020101021226...")
        self.assertEqual(pix["qrcode"], "base64img")
        self.order.refresh_from_db()
        self.assertEqual(self.order.asaas_payment_id, "pay_abc")
        self.assertEqual(self.order.asaas_pix_copy_paste, "00020101021226...")
        self.assertEqual(self.order.payment_provider, PaymentProvider.ASAAS)
        self.assertEqual(self.order.financial_transaction_id, "pay_abc")
        self.assertEqual(self.order.administrative_fee, Decimal("1.99"))
        self.assertEqual(self.order.net_amount, Decimal("148.01"))
        self.assertEqual(self.order.deposit_status, DepositStatus.PENDING)
        self.person.refresh_from_db()
        self.assertEqual(self.person.asaas_customer_id, "cus_123")

    @patch("system.services.asaas_checkout.asaas_client.get_payment")
    @patch("system.services.asaas_checkout.asaas_client.get_pix_qrcode")
    @patch("system.services.asaas_checkout.asaas_client.create_pix_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_reuses_pix_when_not_expired(self, m_customer, m_payment, m_qr, m_get_payment):
        m_customer.return_value = {"id": "cus_1"}
        m_payment.return_value = {"id": "pay_1"}
        m_qr.return_value = {"payload": "code", "encodedImage": "img"}
        m_get_payment.return_value = {"invoiceUrl": "https://sandbox.asaas.com/i/pay_1"}

        first = asaas_checkout.create_pix_charge_for_order(self.order)
        second = asaas_checkout.create_pix_charge_for_order(self.order)

        self.assertEqual(first["payment_id"], second["payment_id"])
        self.assertTrue(second["reused"])
        self.assertEqual(m_payment.call_count, 1)

    def test_rejects_paid_order(self):
        self.order.payment_status = PaymentStatus.PAID
        self.order.save()
        with self.assertRaises(asaas_checkout.AsaasCheckoutError):
            asaas_checkout.create_pix_charge_for_order(self.order)

    @patch(
        "system.services.asaas_checkout.asaas_client.create_customer",
        side_effect=AsaasClientError("falha sim"),
    )
    def test_propagates_client_errors(self, _):
        with self.assertRaises(asaas_checkout.AsaasCheckoutError):
            asaas_checkout.create_pix_charge_for_order(self.order)

    @patch("system.services.asaas_checkout.asaas_client.create_credit_card_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_create_credit_card_charge_uses_asaas_invoice_url(self, m_customer, m_payment):
        self.plan.billing_cycle = BillingCycle.SEMIANNUAL
        self.plan.payment_method = PlanPaymentMethod.CREDIT_CARD
        self.plan.gateway_code = "asaas_card"
        self.plan.gateway_fixed_fee = Decimal("0.49")
        self.plan.gateway_percentage_fee = Decimal("0.0429")
        self.plan.save()
        m_customer.return_value = {"id": "cus_card"}
        m_payment.return_value = {
            "id": "pay_card",
            "invoiceUrl": "https://sandbox.asaas.com/i/pay_card",
        }

        payment = asaas_checkout.create_credit_card_charge_for_order(self.order)

        self.assertEqual(payment["payment_id"], "pay_card")
        self.assertEqual(payment["invoice_url"], "https://sandbox.asaas.com/i/pay_card")
        m_payment.assert_called_once()
        payload = m_payment.call_args.kwargs
        self.assertEqual(payload["customer_id"], "cus_card")
        self.assertEqual(payload["installment_count"], 6)
        self.order.refresh_from_db()
        self.assertEqual(self.order.asaas_payment_id, "pay_card")
        self.assertEqual(self.order.payment_provider, PaymentProvider.ASAAS)
        self.assertEqual(self.order.financial_transaction_id, "pay_card")

    @patch("system.services.asaas_checkout.asaas_client._request")
    def test_create_credit_card_payment_sends_total_value_only_for_installments(self, mock_request):
        mock_request.return_value = {"id": "pay_1"}

        asaas_client.create_credit_card_payment(
            customer_id="cus_1",
            value=Decimal("1200.00"),
            due_date=date(2026, 5, 20),
            description="Pedido teste",
            external_reference=10,
            installment_count=6,
        )

        body = mock_request.call_args.kwargs["json_body"]
        self.assertEqual(body["billingType"], "CREDIT_CARD")
        self.assertEqual(body["installmentCount"], 6)
        self.assertEqual(body["totalValue"], 1200.0)
        self.assertNotIn("value", body)

    @patch("system.services.asaas_checkout.asaas_client._request")
    def test_create_credit_card_payment_sends_value_for_single_charge(self, mock_request):
        mock_request.return_value = {"id": "pay_1"}

        asaas_client.create_credit_card_payment(
            customer_id="cus_1",
            value=Decimal("230.38"),
            due_date=date(2026, 5, 20),
            installment_count=1,
        )

        body = mock_request.call_args.kwargs["json_body"]
        self.assertEqual(body["billingType"], "CREDIT_CARD")
        self.assertEqual(body["value"], 230.38)
        self.assertNotIn("installmentCount", body)
        self.assertNotIn("totalValue", body)


@override_settings(
    ASAAS_API_KEY="test-key",
    ASAAS_WEBHOOK_TOKEN="wh-token",
    ASAAS_API_URL="https://sandbox.asaas.com/api/v3",
)
class AsaasCheckoutPlanPriceCatalogTests(TestCase):
    """PRD-137: pedidos do catálogo PlanTier/PlanPrice (Individual/Kids/Juvenil,
    usado pelo cadastro público desde a PRD-129) ficavam presos em 1x — o cálculo
    de parcelamento só olhava para RegistrationOrder.plan (SubscriptionPlan
    legado, hoje só Veterano), nunca para plan_price_ref."""

    def setUp(self):
        self.person = _make_person()
        self.tier = PlanTier.objects.create(
            code="adult-2x-installments",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.plan_price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            billing_cycle=BillingCycle.SEMIANNUAL,
            gateway_code="asaas_card",
            base_monthly_net_price=Decimal("216.42"),
            cycle_discount_percentage=Decimal("0.0774"),
            gateway_fixed_fee=Decimal("0.49"),
            gateway_percentage_fee=Decimal("0.0429"),
        )
        self.order = RegistrationOrder.objects.create(
            person=self.person,
            plan_price_ref=self.plan_price,
            plan_price=self.plan_price.price,
            total=self.plan_price.price,
        )

    def test_max_installments_resolves_cycle_from_plan_price_ref(self):
        self.assertIsNone(self.order.plan)
        self.assertEqual(asaas_checkout._max_installments_for_order(self.order), 6)

    def test_installment_options_resolve_cycle_from_plan_price_ref(self):
        options = asaas_checkout.get_installment_options_for_order(self.order)

        self.assertEqual([o["count"] for o in options], [1, 2, 3, 6])

    @patch("system.services.asaas_checkout.asaas_client.create_credit_card_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_create_credit_card_charge_uses_plan_price_cycle_for_installments(
        self, m_customer, m_payment
    ):
        m_customer.return_value = {"id": "cus_pp"}
        m_payment.return_value = {
            "id": "pay_pp",
            "invoiceUrl": "https://sandbox.asaas.com/i/pay_pp",
        }

        asaas_checkout.create_credit_card_charge_for_order(self.order)

        payload = m_payment.call_args.kwargs
        self.assertEqual(payload["installment_count"], 6)


class AsaasClientTests(TestCase):
    @patch("system.services.asaas_client._request")
    def test_get_payment_statistics_uses_finance_statistics_endpoint(self, mock_request):
        mock_request.return_value = {
            "quantity": 2,
            "value": 100,
            "netValue": 98,
        }

        result = asaas_client.get_payment_statistics(status="PENDING")

        self.assertEqual(result["netValue"], 98)
        mock_request.assert_called_once_with(
            "GET",
            "/finance/payment/statistics",
            params={"status": "PENDING"},
        )


@override_settings(ASAAS_API_KEY="k", ASAAS_WEBHOOK_TOKEN="wh")
class AsaasPayrollTests(TestCase):
    def setUp(self):
        self.person = _make_person(full_name="Professor Um", cpf="99999999999")
        self.bank = TeacherBankAccount.objects.create(
            person=self.person,
            pix_key="99999999999",
            pix_key_type=PixKeyType.CPF,
        )
        self.config = TeacherPayrollConfig.objects.create(
            person=self.person,
            monthly_salary=Decimal("2500.00"),
            payment_day=15,
        )

    def test_schedule_creates_pending_payout(self):
        today = date(2026, 4, 15)
        result = asaas_payroll.schedule_monthly_payouts(today=today)
        self.assertEqual(len(result), 1)
        payout = TeacherPayout.objects.get()
        self.assertEqual(payout.status, PayoutStatus.PENDING)
        self.assertEqual(payout.reference_month, date(2026, 4, 1))
        self.assertEqual(payout.amount, Decimal("2500.00"))

    def test_schedule_is_idempotent(self):
        today = date(2026, 4, 15)
        asaas_payroll.schedule_monthly_payouts(today=today)
        second = asaas_payroll.schedule_monthly_payouts(today=today)
        self.assertEqual(second, [])
        self.assertEqual(TeacherPayout.objects.count(), 1)

    def test_schedule_skips_wrong_day(self):
        today = date(2026, 4, 10)
        result = asaas_payroll.schedule_monthly_payouts(today=today)
        self.assertEqual(result, [])

    def test_schedule_skips_zero_amount_payroll(self):
        self.config.monthly_salary = Decimal("0.00")
        self.config.save(update_fields=["monthly_salary", "updated_at"])

        result = asaas_payroll.schedule_monthly_payouts(today=date(2026, 4, 15))

        self.assertEqual(result, [])
        self.assertFalse(TeacherPayout.objects.exists())

    def test_approve_then_dispatch_flow(self):
        payout = TeacherPayout.objects.create(
            person=self.person,
            bank_account=self.bank,
            kind=PayoutKind.PAYROLL,
            reference_month=date(2026, 4, 1),
            amount=Decimal("2500.00"),
            status=PayoutStatus.PENDING,
        )
        asaas_payroll.approve_payout(payout, admin_user=None, notes="ok")
        self.assertEqual(payout.status, PayoutStatus.APPROVED)

        with patch(
            "system.services.asaas_payroll.asaas_client.create_transfer",
            return_value={"id": "trf_1"},
        ) as m_trf:
            asaas_payroll.dispatch_payout(payout)
            m_trf.assert_called_once()
        self.assertEqual(payout.status, PayoutStatus.SENT)
        self.assertEqual(payout.asaas_transfer_id, "trf_1")

    def test_dispatch_failure_marks_failed(self):
        payout = TeacherPayout.objects.create(
            person=self.person,
            bank_account=self.bank,
            kind=PayoutKind.PAYROLL,
            reference_month=date(2026, 4, 1),
            amount=Decimal("2500.00"),
            status=PayoutStatus.APPROVED,
        )
        with patch(
            "system.services.asaas_payroll.asaas_client.create_transfer",
            side_effect=AsaasClientError("saldo insuficiente"),
        ):
            with self.assertRaises(asaas_payroll.PayrollError):
                asaas_payroll.dispatch_payout(payout)
        payout.refresh_from_db()
        self.assertEqual(payout.status, PayoutStatus.FAILED)
        self.assertIn("saldo", payout.failure_reason)

    def test_cannot_dispatch_pending(self):
        payout = TeacherPayout.objects.create(
            person=self.person,
            bank_account=self.bank,
            kind=PayoutKind.PAYROLL,
            reference_month=date(2026, 4, 1),
            amount=Decimal("2500.00"),
            status=PayoutStatus.PENDING,
        )
        with self.assertRaises(asaas_payroll.PayrollError):
            asaas_payroll.dispatch_payout(payout)


@override_settings(ASAAS_API_KEY="k", ASAAS_WEBHOOK_TOKEN="wh")
class AsaasWebhookTests(TestCase):
    def setUp(self):
        self.person = _make_person()
        self.plan = SubscriptionPlan.objects.create(
            code="mensal",
            display_name="Mensal",
            price=Decimal("100.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        self.order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("100.00"),
            total=Decimal("100.00"),
            asaas_payment_id="pay_x",
        )
        self.bank = TeacherBankAccount.objects.create(
            person=self.person,
            pix_key="key",
            pix_key_type=PixKeyType.EVP,
        )
        self.payout = TeacherPayout.objects.create(
            person=self.person,
            bank_account=self.bank,
            kind=PayoutKind.PAYROLL,
            reference_month=date(2026, 4, 1),
            amount=Decimal("2000.00"),
            status=PayoutStatus.SENT,
            asaas_transfer_id="trf_x",
        )

    def test_payment_received_marks_order_paid(self):
        event = {
            "id": "evt_1",
            "event": "PAYMENT_RECEIVED",
            "payment": {"id": "pay_x"},
        }
        result = asaas_webhooks.process_asaas_event(event)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, PaymentStatus.PAID)
        self.assertIsNotNone(self.order.paid_at)
        self.assertEqual(result["order"], self.order)
        self.assertFalse(result["duplicate"])
        membership = Membership.objects.get(person=self.person, plan=self.plan)
        self.assertEqual(membership.status, MembershipStatus.ACTIVE)
        self.assertIsNotNone(membership.current_period_end)

    def test_webhook_is_idempotent(self):
        event = {
            "id": "evt_dup",
            "event": "PAYMENT_CONFIRMED",
            "payment": {"id": "pay_x"},
        }
        asaas_webhooks.process_asaas_event(event)
        result = asaas_webhooks.process_asaas_event(event)
        self.assertTrue(result["duplicate"])

    def test_transfer_done_marks_payout_paid(self):
        event = {
            "id": "evt_trf",
            "event": "TRANSFER_DONE",
            "transfer": {"id": "trf_x"},
        }
        asaas_webhooks.process_asaas_event(event)
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, PayoutStatus.PAID)

    def test_transfer_failed_marks_payout_failed(self):
        event = {
            "id": "evt_fail",
            "event": "TRANSFER_FAILED",
            "transfer": {"id": "trf_x", "failReason": "invalid key"},
        }
        asaas_webhooks.process_asaas_event(event)
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, PayoutStatus.FAILED)
        self.assertIn("invalid", self.payout.failure_reason)

    def test_payment_refunded_records_payroll_adjustment(self):
        self.order.payment_status = PaymentStatus.PAID
        self.order.paid_at = timezone.now()
        self.order.net_amount = Decimal("98.01")
        self.order.save(
            update_fields=[
                "payment_status",
                "paid_at",
                "net_amount",
                "updated_at",
            ]
        )
        event = {
            "id": "evt_refund",
            "event": "PAYMENT_REFUNDED",
            "payment": {"id": "pay_x"},
        }

        result = asaas_webhooks.process_asaas_event(event)

        self.order.refresh_from_db()
        self.assertEqual(result["order"], self.order)
        self.assertEqual(self.order.payment_status, PaymentStatus.REFUNDED)
        self.assertIsNotNone(self.order.refunded_at)
        self.assertIn("PAYROLL_REFUND_ADJUSTMENT", self.order.notes)
        self.assertIn('"amount": "100.00"', self.order.notes)

    def test_payment_partially_refunded_records_partial_payroll_adjustment(self):
        self.order.payment_status = PaymentStatus.PAID
        self.order.paid_at = timezone.now()
        self.order.save(update_fields=["payment_status", "paid_at", "updated_at"])
        event = {
            "id": "evt_partial_refund",
            "event": "PAYMENT_PARTIALLY_REFUNDED",
            "payment": {"id": "pay_x", "refundedValue": "40.00"},
        }

        asaas_webhooks.process_asaas_event(event)

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, PaymentStatus.PAID)
        self.assertIsNotNone(self.order.refunded_at)
        self.assertIn("PAYROLL_REFUND_ADJUSTMENT", self.order.notes)
        self.assertIn('"amount": "40.00"', self.order.notes)

    def test_withdrawal_service_is_removed(self):
        self.assertFalse(hasattr(asaas_payroll, "request_withdrawal"))

    def test_unknown_payment_id_ignored(self):
        event = {
            "id": "evt_unknown",
            "event": "PAYMENT_RECEIVED",
            "payment": {"id": "pay_zzz"},
        }
        result = asaas_webhooks.process_asaas_event(event)
        self.assertIsNone(result["order"])

    def test_payment_created_is_non_actionable_and_not_persisted(self):
        event = {
            "id": "evt_created",
            "event": "PAYMENT_CREATED",
            "payment": {"id": "pay_x"},
        }
        result = asaas_webhooks.process_asaas_event(event)
        self.assertFalse(result["duplicate"])
        self.assertIsNone(result["order"])

    def test_event_claim_lock_aborts_transaction_for_retry(self):
        event = {
            "id": "evt_locked",
            "event": "PAYMENT_RECEIVED",
            "payment": {"id": "pay_x"},
        }
        with patch.object(
            asaas_webhooks.AsaasWebhookEvent.objects,
            "create",
            side_effect=OperationalError("database is locked"),
        ):
            with self.assertRaises(OperationalError):
                asaas_webhooks.process_asaas_event(event)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, PaymentStatus.PENDING)
