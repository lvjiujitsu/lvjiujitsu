from datetime import date
from decimal import Decimal

import stripe
from django.test import TestCase
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    RegistrationOrder,
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod
from system.models.registration_order import PaymentProvider, PaymentStatus
from system.services.membership import (
    activate_membership_from_paid_order,
    mark_membership_canceled,
    record_invoice_from_stripe,
    upsert_membership_from_stripe_subscription,
)


def _stripe_invoice(payload):
    return stripe.Invoice.construct_from(payload, "sk_test_dummy")


def _stripe_subscription(payload):
    return stripe.Subscription.construct_from(payload, "sk_test_dummy")


class ActivateMembershipStripeSyncTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Pessoa Sync Stripe",
            cpf="529.982.247-25",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="plan-sync-stripe",
            display_name="Plano Sync Stripe",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("199.00"),
            gateway_code="stripe_card",
        )

    def test_activate_membership_stores_stripe_subscription_id_when_provided(self):
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=self.plan.price,
            total=self.plan.price,
            payment_status=PaymentStatus.PAID,
            paid_at=timezone.now(),
            payment_provider=PaymentProvider.STRIPE,
        )

        membership = activate_membership_from_paid_order(
            order,
            stripe_subscription_id="sub_owner_123",
            stripe_subscription_item_id="si_dependent_456",
        )

        self.assertEqual(membership.stripe_subscription_id, "sub_owner_123")
        self.assertEqual(membership.stripe_subscription_item_id, "si_dependent_456")

    def test_activate_membership_without_stripe_ids_leaves_them_blank(self):
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=self.plan.price,
            total=self.plan.price,
            payment_status=PaymentStatus.PAID,
            paid_at=timezone.now(),
            payment_provider=PaymentProvider.ASAAS,
        )

        membership = activate_membership_from_paid_order(order)

        self.assertEqual(membership.stripe_subscription_id, "")
        self.assertEqual(membership.stripe_subscription_item_id, "")


class SharedSubscriptionWebhookTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.owner = Person.objects.create(
            full_name="Titular Assinatura Compartilhada",
            cpf="529.982.247-25",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Assinatura Compartilhada",
            cpf="153.509.460-56",
            person_type=self.person_type,
            birth_date=date(2012, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.owner_plan = SubscriptionPlan.objects.create(
            code="plan-owner-shared",
            display_name="Plano Titular Compartilhado",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("199.00"),
            gateway_code="stripe_card",
        )
        self.dependent_plan = SubscriptionPlan.objects.create(
            code="plan-dependent-shared",
            display_name="Plano Dependente Compartilhado",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("120.00"),
            gateway_code="stripe_card",
        )
        self.owner_membership = Membership.objects.create(
            person=self.owner,
            plan=self.owner_plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_shared_1",
            stripe_subscription_item_id="si_owner_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        self.dependent_membership = Membership.objects.create(
            person=self.dependent,
            plan=self.dependent_plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_shared_1",
            stripe_subscription_item_id="si_dependent_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

    def test_record_invoice_from_stripe_splits_multi_line_invoice_across_memberships(self):
        invoice = _stripe_invoice({
            "id": "in_shared_1",
            "subscription": "sub_shared_1",
            "amount_paid": 31900,
            "currency": "brl",
            "status": "paid",
            "hosted_invoice_url": "",
            "payment_intent": "pi_shared_1",
            "description": "",
            "status_transitions": {"paid_at": int(timezone.now().timestamp())},
            "lines": {
                "data": [
                    {
                        "subscription_item": "si_owner_1",
                        "amount": 19900,
                        "period": {"start": 1700000000, "end": 1702592000},
                    },
                    {
                        "subscription_item": "si_dependent_1",
                        "amount": 12000,
                        "period": {"start": 1700000000, "end": 1702592000},
                    },
                ]
            },
        })

        first_invoice = record_invoice_from_stripe(invoice)

        self.assertIsNotNone(first_invoice)
        owner_invoice = self.owner_membership.invoices.get()
        dependent_invoice = self.dependent_membership.invoices.get()
        self.assertEqual(owner_invoice.amount_paid, Decimal("199.00"))
        self.assertEqual(dependent_invoice.amount_paid, Decimal("120.00"))
        self.assertNotEqual(owner_invoice.stripe_invoice_id, dependent_invoice.stripe_invoice_id)

    def test_record_invoice_from_stripe_single_membership_uses_invoice_total(self):
        self.dependent_membership.delete()
        invoice = _stripe_invoice({
            "id": "in_single_1",
            "subscription": "sub_shared_1",
            "amount_paid": 19900,
            "currency": "brl",
            "status": "paid",
            "hosted_invoice_url": "",
            "payment_intent": "pi_single_1",
            "description": "",
            "status_transitions": {"paid_at": int(timezone.now().timestamp())},
            "lines": {
                "data": [
                    {
                        "subscription_item": "si_owner_1",
                        "amount": 19900,
                        "period": {"start": 1700000000, "end": 1702592000},
                    },
                ]
            },
        })

        invoice_record = record_invoice_from_stripe(invoice)

        self.assertEqual(invoice_record.amount_paid, Decimal("199.00"))
        self.assertEqual(invoice_record.membership_id, self.owner_membership.pk)
        self.assertEqual(invoice_record.stripe_invoice_id, "in_single_1")

    def test_upsert_membership_from_stripe_subscription_updates_all_shared_memberships(self):
        subscription = _stripe_subscription({
            "id": "sub_shared_1",
            "status": "past_due",
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "cancel_at_period_end": False,
            "canceled_at": None,
        })

        upsert_membership_from_stripe_subscription(subscription)

        self.owner_membership.refresh_from_db()
        self.dependent_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.status, MembershipStatus.PAST_DUE)
        self.assertEqual(self.dependent_membership.status, MembershipStatus.PAST_DUE)

    def test_mark_membership_canceled_cancels_all_shared_memberships(self):
        subscription = _stripe_subscription({
            "id": "sub_shared_1",
            "canceled_at": int(timezone.now().timestamp()),
        })

        mark_membership_canceled(subscription)

        self.owner_membership.refresh_from_db()
        self.dependent_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.status, MembershipStatus.CANCELED)
        self.assertEqual(self.dependent_membership.status, MembershipStatus.CANCELED)
