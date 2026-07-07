from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Membership, MembershipStatus, Person, PersonType
from system.models.membership import (
    MembershipPauseRequest,
    MembershipPauseRequestKind,
    MembershipPauseRequestStatus,
)
from system.models.membership_timeline import (
    MembershipTimelineEvent,
    MembershipTimelineEventType,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanTier, PlanPrice, PlanWeeklyFrequency
from system.models.registration_order import PaymentProvider, PaymentStatus, RegistrationOrder
from system.services.membership_timeline_backfill import backfill_membership_timeline


def _make_person(name, cpf):
    person_type = PersonType.objects.filter(code=PersonTypeCode.STUDENT).first()
    if person_type is None:
        person_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
    return Person.objects.create(
        full_name=name, cpf=cpf, person_type=person_type,
        birth_date=date(1990, 1, 1), biological_sex=BiologicalSex.MALE,
    )


class BackfillMembershipTimelineTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-timeline-backfill",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )

    def test_backfills_membership_cancellation(self):
        person = _make_person("Backfill Cancelamento", "390.533.447-05")
        canceled_at = timezone.now() - timedelta(days=40)
        Membership.objects.create(
            person=person, plan_price=self.price, status=MembershipStatus.CANCELED,
            canceled_at=canceled_at,
        )

        result = backfill_membership_timeline()

        self.assertEqual(result["cancellations"], 1)
        event = MembershipTimelineEvent.objects.get(
            person=person, event_type=MembershipTimelineEventType.MEMBERSHIP_CANCELED
        )
        self.assertEqual(event.created_at, canceled_at)
        self.assertTrue(event.context["backfilled"])

    def test_backfills_order_payment_and_refund(self):
        person = _make_person("Backfill Pagamento", "153.509.460-56")
        paid_at = timezone.now() - timedelta(days=20)
        refunded_at = timezone.now() - timedelta(days=10)
        RegistrationOrder.objects.create(
            person=person, plan_price_ref=self.price, total=Decimal("200.00"),
            payment_status=PaymentStatus.REFUNDED, payment_provider=PaymentProvider.ASAAS,
            paid_at=paid_at, refunded_at=refunded_at,
        )

        result = backfill_membership_timeline()

        self.assertEqual(result["payments"], 1)
        self.assertEqual(result["refunds"], 1)
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=person, event_type=MembershipTimelineEventType.PAYMENT_CONFIRMED
            ).exists()
        )
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=person, event_type=MembershipTimelineEventType.REFUND_ISSUED
            ).exists()
        )

    def test_backfills_pause_requested_and_approved(self):
        person = _make_person("Backfill Pausa", "920.000.011-81")
        membership = Membership.objects.create(
            person=person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(), current_period_end=timezone.now() + timedelta(days=30),
        )
        decided_at = timezone.now() - timedelta(days=5)
        MembershipPauseRequest.objects.create(
            membership=membership,
            kind=MembershipPauseRequestKind.SELF_SERVICE,
            status=MembershipPauseRequestStatus.APPROVED,
            requested_start_date=date.today() - timedelta(days=15),
            requested_end_date=date.today() - timedelta(days=8),
            decided_at=decided_at,
        )

        result = backfill_membership_timeline()

        self.assertEqual(result["pauses"], 2)
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=person, event_type=MembershipTimelineEventType.PAUSE_REQUESTED
            ).exists()
        )
        self.assertTrue(
            MembershipTimelineEvent.objects.filter(
                person=person, event_type=MembershipTimelineEventType.PAUSE_APPROVED
            ).exists()
        )

    def test_running_twice_does_not_duplicate(self):
        person = _make_person("Backfill Idempotente", "283.958.686-00")
        canceled_at = timezone.now() - timedelta(days=40)
        Membership.objects.create(
            person=person, plan_price=self.price, status=MembershipStatus.CANCELED,
            canceled_at=canceled_at,
        )

        first = backfill_membership_timeline()
        second = backfill_membership_timeline()

        self.assertEqual(first["cancellations"], 1)
        self.assertEqual(second["cancellations"], 0)
        self.assertEqual(
            MembershipTimelineEvent.objects.filter(
                event_type=MembershipTimelineEventType.MEMBERSHIP_CANCELED
            ).count(),
            1,
        )

    def test_management_command_runs(self):
        person = _make_person("Backfill Command", "845.669.360-05")
        Membership.objects.create(
            person=person, plan_price=self.price, status=MembershipStatus.CANCELED,
            canceled_at=timezone.now() - timedelta(days=5),
        )
        out = StringIO()
        call_command("backfill_membership_timeline", stdout=out)
        self.assertIn("Concluído", out.getvalue())
