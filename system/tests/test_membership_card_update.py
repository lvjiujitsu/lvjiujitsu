
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipInvoice,
    MembershipStatus,
    Person,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
)
from system.models.membership_timeline import (
    MembershipTimelineEvent,
    MembershipTimelineEventType,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.models.registration_order import OrderKind, PaymentStatus, RegistrationOrder
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.membership import (
    activate_membership_from_paid_order,
    extract_stripe_subscription_period,
    mark_invoice_failed,
    upsert_membership_from_stripe_subscription,
)
from system.services.stripe_checkout import (
    StripeCheckoutError,
    create_billing_portal_session,
    get_membership_default_payment_method_id,
)
from system.services.stripe_webhooks import _handle_pre_registration_checkout_completed


def _stripe_subscription(payload):
    return stripe.Subscription.construct_from(payload, "sk_test_dummy")


class MembershipPaymentLabelTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-label-test", display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT, weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.person = Person.objects.create(
            full_name="Aluno Label Teste", cpf="529.982.247-25",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def _membership(self, *, payment_method, gateway_code, stripe_subscription_id=""):
        price = PlanPrice.objects.create(
            tier=self.tier, payment_method=payment_method, gateway_code=gateway_code,
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        now = timezone.now()
        return Membership.objects.create(
            person=self.person, plan_price=price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
            stripe_subscription_id=stripe_subscription_id,
        )

    def test_stripe_recurring_label_and_flag(self):
        m = self._membership(
            payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            stripe_subscription_id="sub_123",
        )
        self.assertEqual(m.effective_payment_summary_label, "Cartão de crédito · Stripe (recorrente)")
        self.assertTrue(m.is_stripe_recurring)

    def test_asaas_pix_label(self):
        m = self._membership(payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix")
        self.assertEqual(m.effective_payment_summary_label, "PIX · Asaas")
        self.assertFalse(m.is_stripe_recurring)

    def test_asaas_card_label(self):
        m = self._membership(payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="asaas_card")
        self.assertEqual(m.effective_payment_summary_label, "Cartão de crédito · Asaas")
        self.assertFalse(m.is_stripe_recurring)


class MarkInvoiceFailedHistoryTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-invoice-fail-test", display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT, weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Fatura Falhada", cpf="960.013.389-14",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
            stripe_subscription_id="sub_fail_test",
        )

    def test_mark_invoice_failed_records_history_entry(self):
        stripe_invoice = {
            "id": "in_test_failed_1",
            "subscription": "sub_fail_test",
            "amount_due": 23037,
            "currency": "brl",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test",
        }
        mark_invoice_failed(stripe_invoice)

        self.membership.refresh_from_db()
        self.assertEqual(self.membership.status, MembershipStatus.PAST_DUE)

        invoice = MembershipInvoice.objects.get(stripe_invoice_id="in_test_failed_1")
        self.assertEqual(invoice.status, "failed")
        self.assertEqual(invoice.amount_paid, Decimal("0"))
        self.assertIsNone(invoice.paid_at)

    def test_home_renders_after_failed_invoice_for_plan_price_membership(self):
        mark_invoice_failed({
            "id": "in_test_home_render_1", "subscription": "sub_fail_test", "amount_due": 23037,
        })
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Falhou")

    def test_same_invoice_later_paid_updates_existing_entry(self):
        from system.services.membership import record_invoice_from_stripe

        mark_invoice_failed({
            "id": "in_test_retry_1", "subscription": "sub_fail_test", "amount_due": 23037,
        })
        self.assertEqual(MembershipInvoice.objects.filter(stripe_invoice_id="in_test_retry_1").count(), 1)

        record_invoice_from_stripe({
            "id": "in_test_retry_1", "subscription": "sub_fail_test", "amount_paid": 23037,
            "status": "paid",
        })

        invoice = MembershipInvoice.objects.get(stripe_invoice_id="in_test_retry_1")
        self.assertEqual(invoice.status, "paid")
        self.assertEqual(invoice.amount_paid, Decimal("230.37"))
        self.assertEqual(MembershipInvoice.objects.filter(stripe_invoice_id="in_test_retry_1").count(), 1)


class CreateBillingPortalSessionTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-portal-test", display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT, weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Portal Teste", cpf="153.509.460-56",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
            stripe_subscription_id="sub_portal_test", stripe_customer_id="cus_portal_test",
        )

    def test_raises_without_stripe_customer(self):
        self.membership.stripe_customer_id = ""
        self.membership.save()
        request = MagicMock(build_absolute_uri=lambda path: f"http://testserver{path}")
        with self.assertRaises(StripeCheckoutError):
            create_billing_portal_session(self.membership, request)

    @patch("system.services.stripe_checkout._get_client")
    def test_creates_session_with_payment_method_update_flow(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.billing_portal.Session.create.return_value = {
            "id": "bps_test_1", "url": "https://billing.stripe.com/p/session/test_1",
        }
        mock_get_client.return_value = mock_client
        request = MagicMock(build_absolute_uri=lambda path: f"http://testserver{path}")

        session = create_billing_portal_session(self.membership, request)

        self.assertEqual(session["url"], "https://billing.stripe.com/p/session/test_1")
        call_kwargs = mock_client.billing_portal.Session.create.call_args.kwargs
        self.assertEqual(call_kwargs["customer"], "cus_portal_test")
        self.assertEqual(call_kwargs["flow_data"], {"type": "payment_method_update"})

    @patch("system.services.stripe_checkout._get_client")
    def test_reads_default_payment_method_from_real_stripe_objects(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.Subscription.retrieve.return_value = stripe.Subscription.construct_from(
            {"id": "sub_portal_test", "default_payment_method": None},
            "sk_test_dummy",
        )
        mock_client.Customer.retrieve.return_value = stripe.Customer.construct_from(
            {
                "id": "cus_portal_test",
                "invoice_settings": {"default_payment_method": "pm_customer"},
            },
            "sk_test_dummy",
        )
        mock_get_client.return_value = mock_client

        payment_method_id = get_membership_default_payment_method_id(self.membership)

        self.assertEqual(payment_method_id, "pm_customer")


class MembershipUpdateCardViewTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-cardview-test", display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT, weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price_stripe = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.price_asaas = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("190.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno View Cartao", cpf="283.958.686-00",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def _create_stripe_membership(self):
        now = timezone.now()
        return Membership.objects.create(
            person=self.person, plan_price=self.price_stripe, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
            stripe_subscription_id="sub_view_test", stripe_customer_id="cus_view_test",
        )

    @patch(
        "system.views.plan_change_views.get_membership_default_payment_method_id",
        return_value="pm_before",
    )
    @patch("system.services.stripe_checkout._get_client")
    def test_redirects_to_billing_portal_without_recording_update(
        self, mock_get_client, _mock_payment_method
    ):
        membership = self._create_stripe_membership()
        mock_client = MagicMock()
        mock_client.billing_portal.Session.create.return_value = {
            "id": "bps_view_1", "url": "https://billing.stripe.com/p/session/view_1",
        }
        mock_get_client.return_value = mock_client

        self._login()
        response = self.client.get(reverse("system:membership-update-card"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://billing.stripe.com/p/session/view_1")
        self.assertFalse(
            MembershipTimelineEvent.objects.filter(
                membership=membership,
                event_type=MembershipTimelineEventType.CARD_UPDATED,
            ).exists()
        )
        self.assertEqual(
            self.client.session["pending_card_update"],
            {
                "membership_id": membership.pk,
                "previous_payment_method_id": "pm_before",
            },
        )

    @patch(
        "system.views.plan_change_views.get_membership_default_payment_method_id",
        return_value="pm_after",
    )
    def test_return_records_update_only_after_payment_method_changed(
        self, _mock_payment_method
    ):
        membership = self._create_stripe_membership()
        self._login()
        session = self.client.session
        session["pending_card_update"] = {
            "membership_id": membership.pk,
            "previous_payment_method_id": "pm_before",
        }
        session.save()

        response = self.client.get(
            reverse("system:membership-update-card"),
            {"card_update": "confirm"},
        )

        self.assertRedirects(response, reverse("system:home"))
        event = MembershipTimelineEvent.objects.get(
            membership=membership,
            event_type=MembershipTimelineEventType.CARD_UPDATED,
        )
        self.assertEqual(
            event.context,
            {
                "previous_payment_method_id": "pm_before",
                "payment_method_id": "pm_after",
            },
        )
        self.assertNotIn("pending_card_update", self.client.session)

    @patch(
        "system.views.plan_change_views.get_membership_default_payment_method_id",
        return_value="pm_before",
    )
    def test_return_without_change_does_not_record_update(self, _mock_payment_method):
        membership = self._create_stripe_membership()
        self._login()
        session = self.client.session
        session["pending_card_update"] = {
            "membership_id": membership.pk,
            "previous_payment_method_id": "pm_before",
        }
        session.save()

        response = self.client.get(
            reverse("system:membership-update-card"),
            {"card_update": "confirm"},
        )

        self.assertRedirects(response, reverse("system:home"))
        self.assertFalse(
            MembershipTimelineEvent.objects.filter(
                membership=membership,
                event_type=MembershipTimelineEventType.CARD_UPDATED,
            ).exists()
        )
        self.assertNotIn("pending_card_update", self.client.session)

    def test_redirects_home_when_not_stripe_membership(self):
        now = timezone.now()
        Membership.objects.create(
            person=self.person, plan_price=self.price_asaas, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
        )
        self._login()
        response = self.client.get(reverse("system:membership-update-card"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("system:home"))


class StripeCustomerIdCapturePropagationTestCase(TestCase):

    def setUp(self):
        from system.models import PreRegistration

        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-customer-capture-test", display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT, weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Captura Customer", cpf="920.000.011-81",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.pre_registration = PreRegistration.objects.create(
            holder_cpf="920.000.011-81",
            form_snapshot={"registration_profile": "holder"},
        )

    def test_checkout_completed_captures_customer_id_into_snapshot(self):
        session = {
            "id": "cs_test_capture_1",
            "client_reference_id": f"pre-registration:{self.pre_registration.pk}:plan",
            "subscription": "sub_capture_1",
            "customer": "cus_capture_1",
        }
        _handle_pre_registration_checkout_completed(session)

        self.pre_registration.refresh_from_db()
        plan_payment = self.pre_registration.form_snapshot["plan_payment"]
        self.assertEqual(plan_payment["stripe_subscription_id"], "sub_capture_1")
        self.assertEqual(plan_payment["stripe_customer_id"], "cus_capture_1")

    def test_activate_membership_from_paid_order_sets_customer_id(self):
        order = RegistrationOrder.objects.create(
            person=self.person, plan_price_ref=self.price, plan_price=self.price.price,
            total=self.price.price, kind=OrderKind.SUBSCRIPTION,
            payment_status=PaymentStatus.PAID, paid_at=timezone.now(),
        )
        membership = activate_membership_from_paid_order(
            order,
            stripe_subscription_id="sub_capture_2",
            stripe_customer_id="cus_capture_2",
        )
        self.assertEqual(membership.stripe_subscription_id, "sub_capture_2")
        self.assertEqual(membership.stripe_customer_id, "cus_capture_2")

    def test_dependent_create_paid_plan_order_propagates_customer_id(self):
        from system.services.dependent_registration import _create_paid_plan_order

        guardian_type = PersonType.objects.create(code="guardian-capture-dep-test", display_name="Responsável")
        dependent_type = PersonType.objects.create(code="dependent-capture-test", display_name="Dependente")
        guardian = Person.objects.create(
            full_name="Responsável Captura Teste", cpf="153.509.460-56",
            person_type=guardian_type, birth_date=date(1980, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        dependent = Person.objects.create(
            full_name="Dependente Captura Teste", cpf="920.000.012-62",
            person_type=dependent_type, birth_date=date(2000, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        order = _create_paid_plan_order(
            dependent, self.price,
            checkout_action="stripe_card",
            stripe_subscription_id="sub_dep_capture_1",
            stripe_customer_id="cus_dep_capture_1",
        )
        membership = Membership.objects.get(person=dependent)
        self.assertEqual(membership.stripe_subscription_id, "sub_dep_capture_1")
        self.assertEqual(membership.stripe_customer_id, "cus_dep_capture_1")


class ExtractStripeSubscriptionPeriodTestCase(TestCase):

    def test_reads_top_level_fields_when_present(self):
        sub = _stripe_subscription({
            "id": "sub_period_top", "status": "active",
            "current_period_start": 1700000000, "current_period_end": 1702592000,
        })
        start, end = extract_stripe_subscription_period(sub)
        self.assertEqual(start.timestamp(), 1700000000)
        self.assertEqual(end.timestamp(), 1702592000)

    def test_falls_back_to_item_level_when_top_level_absent(self):
        sub = _stripe_subscription({
            "id": "sub_period_item", "status": "active",
            "items": {
                "data": [
                    {"id": "si_1", "current_period_start": 1700000000, "current_period_end": 1702592000},
                ]
            },
        })
        start, end = extract_stripe_subscription_period(sub)
        self.assertEqual(start.timestamp(), 1700000000)
        self.assertEqual(end.timestamp(), 1702592000)

    def test_returns_none_none_when_nothing_available(self):
        sub = _stripe_subscription({"id": "sub_period_empty", "status": "active"})
        start, end = extract_stripe_subscription_period(sub)
        self.assertIsNone(start)
        self.assertIsNone(end)


class UpsertSubscriptionPreservesPeriodTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-upsert-period-test", display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT, weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.CREDIT_CARD, gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Upsert Period", cpf="529.982.247-25",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=20),
            stripe_subscription_id="sub_upsert_period_test",
        )

    def test_event_without_period_data_does_not_null_existing_dates(self):
        original_end = self.membership.current_period_end
        sub = _stripe_subscription({
            "id": "sub_upsert_period_test", "status": "active",
            "cancel_at_period_end": False, "canceled_at": None,
        })
        upsert_membership_from_stripe_subscription(sub)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.current_period_end, original_end)

    def test_event_with_item_level_period_updates_dates(self):
        sub = _stripe_subscription({
            "id": "sub_upsert_period_test", "status": "active",
            "cancel_at_period_end": False, "canceled_at": None,
            "items": {
                "data": [
                    {"id": "si_1", "current_period_start": 1700000000, "current_period_end": 1702592000},
                ]
            },
        })
        upsert_membership_from_stripe_subscription(sub)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.current_period_end.timestamp(), 1702592000)
