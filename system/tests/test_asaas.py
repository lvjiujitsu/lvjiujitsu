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
    RegistrationOrder,
    SubscriptionPlan,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
)
from system.models.registration_order import PaymentStatus
from system.services import asaas_checkout, asaas_payroll, asaas_webhooks
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

    @patch("system.services.asaas_checkout.asaas_client.get_pix_qrcode")
    @patch("system.services.asaas_checkout.asaas_client.create_pix_payment")
    @patch("system.services.asaas_checkout.asaas_client.create_customer")
    def test_reuses_pix_when_not_expired(self, m_customer, m_payment, m_qr):
        m_customer.return_value = {"id": "cus_1"}
        m_payment.return_value = {"id": "pay_1"}
        m_qr.return_value = {"payload": "code", "encodedImage": "img"}

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

    def test_withdrawal_happy_path(self):
        person = _make_person(full_name="Prof Sacador", cpf="11122233344", type_code="instructor")
        TeacherBankAccount.objects.create(
            person=person,
            pix_key="chave",
            pix_key_type=PixKeyType.EVP,
        )
        TeacherPayrollConfig.objects.create(
            person=person,
            monthly_salary=Decimal("3000.00"),
            payment_day=5,
        )
        available, base, committed = asaas_payroll.compute_available_balance(person)
        self.assertEqual(base, Decimal("3000.00"))
        self.assertEqual(committed, Decimal("0"))
        self.assertEqual(available, Decimal("3000.00"))

        payout = asaas_payroll.request_withdrawal(
            person, Decimal("500.00"), notes="emergência"
        )
        self.assertEqual(payout.kind, PayoutKind.WITHDRAWAL)
        self.assertEqual(payout.status, PayoutStatus.PENDING)

        available2, _, committed2 = asaas_payroll.compute_available_balance(person)
        self.assertEqual(committed2, Decimal("500.00"))
        self.assertEqual(available2, Decimal("2500.00"))

    def test_withdrawal_exceeds_balance(self):
        person = _make_person(full_name="P2", cpf="11122233300", type_code="instructor")
        TeacherBankAccount.objects.create(
            person=person,
            pix_key="x",
            pix_key_type=PixKeyType.EVP,
        )
        TeacherPayrollConfig.objects.create(
            person=person,
            monthly_salary=Decimal("1000.00"),
            payment_day=5,
        )
        with self.assertRaises(asaas_payroll.PayrollError):
            asaas_payroll.request_withdrawal(person, Decimal("2000.00"))

    def test_withdrawal_without_bank_account(self):
        person = _make_person(full_name="P3", cpf="11122233311", type_code="instructor")
        TeacherPayrollConfig.objects.create(
            person=person,
            monthly_salary=Decimal("1000.00"),
            payment_day=5,
        )
        with self.assertRaises(asaas_payroll.PayrollError):
            asaas_payroll.request_withdrawal(person, Decimal("100.00"))

    def test_withdrawal_without_config(self):
        person = _make_person(full_name="P4", cpf="11122233322", type_code="instructor")
        with self.assertRaises(asaas_payroll.PayrollError):
            asaas_payroll.request_withdrawal(person, Decimal("100.00"))

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
