from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
    RegistrationOrder,
    SubscriptionPlan,
)
from system.models.membership import (
    MembershipPauseRequestKind,
    MembershipPauseRequestStatus,
)
from system.models.membership_timeline import (
    MembershipTimelineEvent,
    MembershipTimelineEventType,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.models.registration_order import PaymentProvider, PaymentStatus
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY
from system.services.membership import (
    activate_membership_from_paid_order,
    mark_invoice_failed,
    mark_membership_canceled,
)
from system.services.membership_pause import (
    approve_pause_request,
    create_pause_request,
    reject_pause_request,
)
from system.services.membership_timeline import (
    build_admin_timeline,
    build_client_timeline,
    describe_for_admin,
    describe_for_client,
    record_membership_event,
)
from system.services.plan_change import apply_plan_change
from system.services.stripe_admin_actions import (
    cancel_membership,
    change_membership_plan,
    refund_order,
)


def _make_person(name, cpf):
    person_type = PersonType.objects.filter(code=PersonTypeCode.STUDENT).first()
    if person_type is None:
        person_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
    return Person.objects.create(
        full_name=name,
        cpf=cpf,
        person_type=person_type,
        birth_date=date(1990, 1, 1),
        biological_sex=BiologicalSex.MALE,
    )


class RecordMembershipEventTestCase(TestCase):
    def test_record_membership_event_creates_row(self):
        person = _make_person("Titular Timeline Basico", "390.533.447-05")
        event = record_membership_event(
            person,
            MembershipTimelineEventType.CARD_UPDATED,
            actor=person,
            context={"foo": "bar"},
        )
        self.assertEqual(MembershipTimelineEvent.objects.count(), 1)
        self.assertEqual(event.person, person)
        self.assertEqual(event.event_type, MembershipTimelineEventType.CARD_UPDATED)
        self.assertEqual(event.context, {"foo": "bar"})


class DescribeEventTestCase(TestCase):
    def setUp(self):
        self.person = _make_person("Titular Timeline Describe", "153.509.460-56")

    def test_client_and_admin_descriptions_differ_and_hide_technical_ids(self):
        event = record_membership_event(
            self.person,
            MembershipTimelineEventType.MEMBERSHIP_CANCELED,
            actor=None,
            context={"plan_name": "Adulto 2x", "stripe_subscription_id": "sub_secret_123"},
        )
        client_text = describe_for_client(event)
        admin_text = describe_for_admin(event)
        self.assertNotIn("sub_secret_123", client_text)
        self.assertIn("sub_secret_123", admin_text)
        self.assertNotEqual(client_text, admin_text)

    def test_family_discount_changed_client_text_reflects_direction(self):
        applied = record_membership_event(
            self.person,
            MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED,
            context={"discount_applied": True, "old_price": "200.00", "new_price": "164.00"},
        )
        removed = record_membership_event(
            self.person,
            MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED,
            context={"discount_applied": False, "old_price": "164.00", "new_price": "200.00"},
        )
        self.assertIn("passou a valer", describe_for_client(applied))
        self.assertIn("deixou de valer", describe_for_client(removed))


class DependentAddRemoveTimelineTestCase(TestCase):
    def setUp(self):
        from system.services.dependent_registration import finalize_dependent_registration
        from system.services.registration import ensure_default_person_types

        ensure_default_person_types()
        self.finalize_dependent_registration = finalize_dependent_registration
        self.tier = PlanTier.objects.create(
            code="adult-2x-timeline-dependent",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.owner = _make_person("Titular Timeline Dependente", "920.000.011-81")
        self.account = PortalAccount(person=self.owner)
        self.account.set_password("123456")
        self.account.save()

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_dependent_add_and_remove_emit_events_for_both(self):
        cleaned_data = {
            "dependent_name": "Dependente Timeline Teste",
            "dependent_cpf": "283.958.686-00",
            "dependent_email": "",
            "dependent_phone": "",
            "dependent_birthdate": date(2010, 1, 1),
            "dependent_biological_sex": BiologicalSex.MALE,
            "dependent_password": "123456",
            "dependent_kinship_type": "child",
            "use_family_plan": True,
        }
        result = self.finalize_dependent_registration(self.owner, cleaned_data)
        dependent = result["dependent"]

        added_events = MembershipTimelineEvent.objects.filter(
            event_type=MembershipTimelineEventType.DEPENDENT_ADDED
        )
        self.assertEqual(added_events.filter(person=self.owner).count(), 1)
        self.assertEqual(added_events.filter(person=dependent).count(), 1)

        self._login()
        response = self.client.post(
            reverse("system:dependent-remove", args=[dependent.pk])
        )
        self.assertEqual(response.status_code, 302)

        removed_events = MembershipTimelineEvent.objects.filter(
            event_type=MembershipTimelineEventType.DEPENDENT_REMOVED
        )
        self.assertEqual(removed_events.filter(person=self.owner).count(), 1)
        self.assertEqual(removed_events.filter(person=dependent).count(), 1)


class PauseTimelineTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-timeline-pause",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person = _make_person("Aluno Timeline Pausa", "529.982.247-25")
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10),
            current_period_end=now + timedelta(days=20),
            activated_at=now - timedelta(days=100),
        )

    def test_pause_requested_approved_events(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=9)
        pause = create_pause_request(
            self.membership,
            kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start,
            end_date=end,
        )
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=self.person, event_type=MembershipTimelineEventType.PAUSE_REQUESTED
            ).exists()
        )
        approve_pause_request(pause.pk, approved_by=self.person)
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=self.person, event_type=MembershipTimelineEventType.PAUSE_APPROVED
            ).exists()
        )

    def test_pause_rejected_event(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=9)
        pause = create_pause_request(
            self.membership,
            kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start,
            end_date=end,
        )
        reject_pause_request(pause.pk, rejected_by=self.person, decision_notes="Não aprovado.")
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=self.person, event_type=MembershipTimelineEventType.PAUSE_REJECTED
            ).exists()
        )


class PlanChangeTimelineTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-timeline-planchange",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.old_price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.tier2 = PlanTier.objects.create(
            code="adult-5x-timeline-planchange",
            display_name="Adulto 5x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
        )
        self.new_price = PlanPrice.objects.create(
            tier=self.tier2,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("250.00"),
        )
        self.person = _make_person("Aluno Timeline Troca Plano", "111.222.333-44")
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person,
            plan_price=self.old_price,
            status=MembershipStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            activated_at=now,
        )

    def test_self_service_plan_change_emits_event(self):
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan_price_ref=self.new_price,
            total=self.new_price.price,
            payment_status=PaymentStatus.PAID,
            paid_at=timezone.now(),
            payment_provider=PaymentProvider.ASAAS,
            is_plan_change=True,
        )
        apply_plan_change(order, self.membership, self.new_price)
        event = MembershipTimelineEvent.objects.filter(
            person=self.person, event_type=MembershipTimelineEventType.PLAN_CHANGED
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["new_plan_name"], self.new_price.display_name)

    @patch("system.services.stripe_admin_actions.stripe.Subscription.modify")
    @patch("system.services.stripe_admin_actions.stripe.Subscription.retrieve")
    @override_settings(STRIPE_SECRET_KEY="sk_test_dummy")
    def test_admin_plan_change_emits_event(self, mocked_retrieve, mocked_modify):
        self.membership.stripe_subscription_id = "sub_timeline_planchange"
        self.membership.plan = SubscriptionPlan.objects.create(
            code="legacy-timeline-planchange",
            display_name="Plano Legado Timeline",
            price="200.00",
        )
        self.membership.plan_price = None
        self.membership.save(update_fields=["stripe_subscription_id", "plan", "plan_price"])

        new_plan = SubscriptionPlan.objects.create(
            code="legacy-timeline-planchange-new",
            display_name="Plano Legado Timeline Novo",
            price="250.00",
            stripe_price_id="price_timeline_new",
        )
        mocked_retrieve.return_value = {"items": {"data": [{"id": "si_timeline_1"}]}}

        admin_user = _make_person("Admin Timeline Troca", "306.174.910-08")
        change_membership_plan(self.membership, new_plan, admin_user=admin_user)

        event = MembershipTimelineEvent.objects.filter(
            person=self.person, event_type=MembershipTimelineEventType.PLAN_CHANGED
        ).first()
        self.assertIsNotNone(event)
        self.assertTrue(event.actor_is_admin)


class CancellationTimelineTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-timeline-cancel",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person = _make_person("Aluno Timeline Cancelamento", "980.056.780-05")
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            activated_at=now,
        )

    def test_admin_cancel_without_stripe_emits_event(self):
        admin_user = _make_person("Admin Timeline Cancela", "845.669.360-05")
        cancel_membership(self.membership, admin_user=admin_user)
        event = MembershipTimelineEvent.objects.filter(
            person=self.person, event_type=MembershipTimelineEventType.MEMBERSHIP_CANCELED
        ).first()
        self.assertIsNotNone(event)
        self.assertTrue(event.actor_is_admin)

    def test_webhook_cancel_emits_event(self):
        self.membership.stripe_subscription_id = "sub_timeline_webhook_cancel"
        self.membership.save(update_fields=["stripe_subscription_id"])
        mark_membership_canceled({"id": "sub_timeline_webhook_cancel", "canceled_at": None})
        event = MembershipTimelineEvent.objects.filter(
            person=self.person, event_type=MembershipTimelineEventType.MEMBERSHIP_CANCELED
        ).first()
        self.assertIsNotNone(event)
        self.assertIsNone(event.actor)


class RefundTimelineTestCase(TestCase):
    @patch("system.services.stripe_admin_actions.stripe.Refund.create")
    @override_settings(STRIPE_SECRET_KEY="sk_test_dummy")
    def test_refund_order_emits_event(self, mocked_create):
        person = _make_person("Aluno Timeline Estorno", "706.393.640-58")
        order = RegistrationOrder.objects.create(
            person=person,
            total=Decimal("200.00"),
            payment_status=PaymentStatus.PAID,
            paid_at=timezone.now(),
            payment_provider=PaymentProvider.STRIPE,
            stripe_payment_intent_id="pi_timeline_refund",
        )
        mocked_create.return_value = {"id": "re_timeline_1", "amount": 20000}

        admin_user = _make_person("Admin Timeline Estorno", "017.928.500-08")
        refund_order(order, admin_user=admin_user)

        event = MembershipTimelineEvent.objects.filter(
            person=person, event_type=MembershipTimelineEventType.REFUND_ISSUED
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(Decimal(event.context["amount"]), Decimal("200.00"))


class PaymentTimelineTestCase(TestCase):
    def test_activate_membership_from_paid_order_emits_payment_confirmed(self):
        tier = PlanTier.objects.create(
            code="adult-2x-timeline-payment",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        price = PlanPrice.objects.create(
            tier=tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        person = _make_person("Aluno Timeline Pagamento", "845.263.870-38")
        order = RegistrationOrder.objects.create(
            person=person,
            plan_price_ref=price,
            total=price.price,
            payment_status=PaymentStatus.PAID,
            paid_at=timezone.now(),
            payment_provider=PaymentProvider.ASAAS,
        )
        activate_membership_from_paid_order(order, notes="Teste timeline.")
        event = MembershipTimelineEvent.objects.filter(
            person=person, event_type=MembershipTimelineEventType.PAYMENT_CONFIRMED
        ).first()
        self.assertIsNotNone(event)

    def test_mark_invoice_failed_emits_payment_failed(self):
        tier = PlanTier.objects.create(
            code="adult-2x-timeline-payment-failed",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        price = PlanPrice.objects.create(
            tier=tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        person = _make_person("Aluno Timeline Falha Pagamento", "552.766.030-09")
        now = timezone.now()
        Membership.objects.create(
            person=person,
            plan_price=price,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_timeline_invoice_failed",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            activated_at=now,
        )
        stripe_invoice = {
            "id": "in_timeline_failed_1",
            "subscription": "sub_timeline_invoice_failed",
            "amount_due": 20000,
            "currency": "brl",
            "hosted_invoice_url": "",
        }
        mark_invoice_failed(stripe_invoice)
        event = MembershipTimelineEvent.objects.filter(
            person=person, event_type=MembershipTimelineEventType.PAYMENT_FAILED
        ).first()
        self.assertIsNotNone(event)


class FamilyDiscountTimelineTestCase(TestCase):
    def test_family_discount_transition_emits_event(self):
        from system.services.family_pricing import recompute_family_discounts_for_person

        tier = PlanTier.objects.create(
            code="adult-2x-timeline-discount",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        price = PlanPrice.objects.create(
            tier=tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        owner = _make_person("Titular Timeline Desconto", "390.881.480-90")
        dependent = _make_person("Dependente Timeline Desconto", "710.130.020-79")
        now = timezone.now()
        Membership.objects.create(
            person=owner, plan_price=price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
        )
        Membership.objects.create(
            person=dependent, plan_price=price, status=MembershipStatus.ACTIVE,
            current_period_start=now, current_period_end=now + timedelta(days=30),
        )
        PersonRelationship.objects.create(
            source_person=owner, target_person=dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        recompute_family_discounts_for_person(owner)

        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=owner, event_type=MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED
            ).exists()
        )
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=dependent, event_type=MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED
            ).exists()
        )


class TimelineIsolationAndOrderingTestCase(TestCase):
    def test_client_timeline_isolated_between_families_and_ordered(self):
        family_a_owner = _make_person("Familia A Titular", "390.533.447-05")
        family_b_owner = _make_person("Familia B Titular", "153.509.460-56")

        older = record_membership_event(
            family_a_owner, MembershipTimelineEventType.CARD_UPDATED, context={}
        )
        older.created_at = timezone.now() - timedelta(days=5)
        older.save(update_fields=["created_at"])
        record_membership_event(
            family_a_owner, MembershipTimelineEventType.DEPENDENT_ADDED,
            context={"dependent_name": "X"},
        )
        record_membership_event(
            family_b_owner, MembershipTimelineEventType.CARD_UPDATED, context={}
        )

        timeline_a = build_client_timeline(family_a_owner)
        timeline_b = build_client_timeline(family_b_owner)

        self.assertEqual(len(timeline_a), 2)
        self.assertEqual(len(timeline_b), 1)
        self.assertGreaterEqual(timeline_a[0]["created_at"], timeline_a[1]["created_at"])

    def test_admin_timeline_filters_by_person_and_event_type(self):
        person_a = _make_person("Admin Filtro Pessoa A", "920.000.011-81")
        person_b = _make_person("Admin Filtro Pessoa B", "283.958.686-00")
        record_membership_event(person_a, MembershipTimelineEventType.CARD_UPDATED, context={})
        record_membership_event(person_b, MembershipTimelineEventType.DEPENDENT_ADDED, context={})

        all_events = build_admin_timeline()
        self.assertEqual(len(all_events), 2)

        filtered_by_person = build_admin_timeline(person=person_a)
        self.assertEqual(len(filtered_by_person), 1)
        self.assertEqual(filtered_by_person[0]["person_name"], person_a.full_name)

        filtered_by_type = build_admin_timeline(
            event_type=MembershipTimelineEventType.DEPENDENT_ADDED
        )
        self.assertEqual(len(filtered_by_type), 1)
        self.assertEqual(filtered_by_type[0]["person_name"], person_b.full_name)


class TimelineViewsSmokeTestCase(TestCase):
    def setUp(self):
        self.person = _make_person("Aluno Timeline View", "306.174.910-08")
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()
        record_membership_event(
            self.person, MembershipTimelineEventType.CARD_UPDATED, actor=self.person, context={}
        )

    def test_client_home_renders_timeline_section(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()
        response = self.client.get(reverse("system:home"))
        self.assertEqual(response.status_code, 200)

    def test_admin_timeline_view_requires_admin_and_renders(self):
        from django.contrib.auth import get_user_model

        admin_user = get_user_model().objects.create_user(
            username="admin-timeline-view",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = admin_user.pk
        session.save()
        response = self.client.get(reverse("system:membership-timeline-admin-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stripe Billing Portal")
        self.assertContains(response, 'class="entity-card membership-timeline-card"')
        self.assertContains(response, "/static/business_rule/css/audit/membership_timeline.css?v=1")
