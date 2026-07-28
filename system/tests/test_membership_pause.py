
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassSchedule,
    IbjjfAgeCategory,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
    WeekdayCode,
)
from system.models.category import CategoryAudience
from system.models.class_schedule import TrainingStyle
from system.models.membership import (
    MembershipPauseRequest,
    MembershipPauseRequestKind,
    MembershipPauseRequestStatus,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.class_calendar import get_today_classes_for_person, perform_checkin
from system.services.membership_pause import (
    SELF_SERVICE_ANNUAL_QUOTA_DAYS,
    approve_pause_request,
    cancel_pause_request,
    create_pause_request,
    get_self_service_quota_summary,
    reject_pause_request,
)


class MembershipPauseServiceTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-pause-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price_asaas = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Pausa Teste",
            cpf="529.982.247-25",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()
        now = timezone.now()
        self.activated_at = now - timedelta(days=100)
        self.membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price_asaas,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10),
            current_period_end=now + timedelta(days=20),
            activated_at=self.activated_at,
        )

    def test_create_self_service_pause_within_quota(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=9)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=end,
        )
        self.assertEqual(pause.status, MembershipPauseRequestStatus.PENDING)
        self.assertEqual(pause.duration_days, 10)

    def test_create_self_service_pause_exceeding_quota_raises(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=29)
        create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=end,
        )
        next_start = end + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_pause_request(
                self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
                start_date=next_start, end_date=next_start + timedelta(days=1),
            )

    def test_create_self_service_pause_blocked_during_fidelity(self):
        self.membership.stripe_subscription_id = "sub_123"
        self.membership.current_period_end = timezone.now() + timedelta(days=200)
        self.membership.save()
        start = timezone.localdate() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_pause_request(
                self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
                start_date=start, end_date=start + timedelta(days=1),
            )

    def test_create_medical_pause_allowed_during_fidelity(self):
        self.membership.stripe_subscription_id = "sub_123"
        self.membership.current_period_end = timezone.now() + timedelta(days=200)
        self.membership.save()
        start = timezone.localdate() + timedelta(days=1)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.MEDICAL,
            start_date=start, end_date=start + timedelta(days=59),
        )
        self.assertEqual(pause.status, MembershipPauseRequestStatus.PENDING)

    def test_create_pause_rejects_overlap(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=4)
        create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=end,
        )
        with self.assertRaises(ValidationError):
            create_pause_request(
                self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
                start_date=start + timedelta(days=2), end_date=end + timedelta(days=2),
            )

    def test_create_pause_rejects_end_before_start(self):
        start = timezone.localdate() + timedelta(days=5)
        with self.assertRaises(ValidationError):
            create_pause_request(
                self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
                start_date=start, end_date=start - timedelta(days=1),
            )

    def test_approve_self_service_pause_postpones_period_end_without_fidelity_extension(self):
        original_period_end = self.membership.current_period_end
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=9)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=end,
        )
        approve_pause_request(pause.pk, approved_by=self.person)

        self.membership.refresh_from_db()
        pause.refresh_from_db()
        self.assertEqual(pause.status, MembershipPauseRequestStatus.APPROVED)
        self.assertEqual(
            self.membership.current_period_end, original_period_end + timedelta(days=10)
        )
        self.assertEqual(self.membership.fidelity_extension_days, 0)

    def test_approve_medical_pause_extends_fidelity(self):
        original_period_end = self.membership.current_period_end
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=59)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.MEDICAL,
            start_date=start, end_date=end,
        )
        approve_pause_request(pause.pk, approved_by=self.person)

        self.membership.refresh_from_db()
        self.assertEqual(self.membership.fidelity_extension_days, 60)
        self.assertEqual(
            self.membership.current_period_end, original_period_end + timedelta(days=60)
        )

    @patch("system.services.stripe_admin_actions._get_client")
    def test_approve_pause_calls_stripe_pause_collection_when_subscription_present(self, mock_client):
        self.membership.stripe_subscription_id = "sub_stripe_pause"
        self.membership.save(update_fields=["stripe_subscription_id"])
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=29)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.MEDICAL,
            start_date=start, end_date=end,
        )
        approve_pause_request(pause.pk, approved_by=self.person)

        mock_client.return_value.Subscription.modify.assert_called_once()
        call_args = mock_client.return_value.Subscription.modify.call_args
        self.assertEqual(call_args.args[0], "sub_stripe_pause")
        self.assertEqual(call_args.kwargs["pause_collection"]["behavior"], "void")

    def test_reject_pause_requires_decision_notes(self):
        start = timezone.localdate() + timedelta(days=1)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=start + timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            reject_pause_request(pause.pk, rejected_by=self.person, decision_notes="")
        reject_pause_request(pause.pk, rejected_by=self.person, decision_notes="Sem justificativa suficiente.")
        pause.refresh_from_db()
        self.assertEqual(pause.status, MembershipPauseRequestStatus.REJECTED)

    def test_cancel_pending_pause(self):
        start = timezone.localdate() + timedelta(days=1)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=start + timedelta(days=1),
        )
        cancel_pause_request(pause.pk, canceled_by=self.person)
        pause.refresh_from_db()
        self.assertEqual(pause.status, MembershipPauseRequestStatus.CANCELED)

    def test_decide_already_decided_request_raises(self):
        start = timezone.localdate() + timedelta(days=1)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=start + timedelta(days=1),
        )
        approve_pause_request(pause.pk, approved_by=self.person)
        with self.assertRaises(ValidationError):
            approve_pause_request(pause.pk, approved_by=self.person)

    def test_quota_summary_resets_on_membership_anniversary(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=9)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.SELF_SERVICE,
            start_date=start, end_date=end,
        )
        approve_pause_request(pause.pk, approved_by=self.person)

        summary_same_year = get_self_service_quota_summary(self.membership, reference_date=end)
        self.assertEqual(summary_same_year["used_days"], 10)
        self.assertEqual(summary_same_year["remaining_days"], SELF_SERVICE_ANNUAL_QUOTA_DAYS - 10)

        next_anniversary = self.activated_at.date().replace(year=self.activated_at.year + 1)
        summary_next_year = get_self_service_quota_summary(
            self.membership, reference_date=next_anniversary + timedelta(days=1)
        )
        self.assertEqual(summary_next_year["used_days"], 0)
        self.assertEqual(summary_next_year["remaining_days"], SELF_SERVICE_ANNUAL_QUOTA_DAYS)


class MembershipPauseCheckinBlockingTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.category = ClassCategory.objects.create(
            code="adult-pause-checkin", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age-pause-checkin", display_name="Adulto",
            audience=CategoryAudience.ADULT, minimum_age=18, maximum_age=99,
        )
        self.group = ClassGroup.objects.create(display_name="Jiu Jitsu", class_category=self.category)
        today = timezone.localdate()
        weekday_map = {
            0: WeekdayCode.MONDAY, 1: WeekdayCode.TUESDAY, 2: WeekdayCode.WEDNESDAY,
            3: WeekdayCode.THURSDAY, 4: WeekdayCode.FRIDAY, 5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        self.schedule = ClassSchedule.objects.create(
            class_group=self.group, weekday=weekday_map[today.weekday()],
            start_time=timezone.now().time(), training_style=TrainingStyle.GI,
        )
        self.person = Person.objects.create(
            full_name="Aluno Pausado Checkin", cpf="960.013.389-14",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        ClassEnrollment.objects.create(person=self.person, class_group=self.group, status="active")
        self.tier = PlanTier.objects.create(
            code="adult-2x-pause-checkin-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10), current_period_end=now + timedelta(days=20),
            activated_at=now - timedelta(days=100),
        )

    def _approve_pause_covering_today(self):
        start = timezone.localdate() - timedelta(days=1)
        end = timezone.localdate() + timedelta(days=1)
        pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.MEDICAL,
            start_date=start, end_date=end,
        )
        approve_pause_request(pause.pk, approved_by=self.person)
        return pause

    def test_perform_checkin_blocked_during_approved_pause(self):
        self._approve_pause_covering_today()
        with self.assertRaises(ValueError):
            perform_checkin(self.person, self.schedule.pk)

    def test_today_classes_expose_membership_paused_state(self):
        pause = self._approve_pause_covering_today()
        entries = get_today_classes_for_person(self.person)
        regular = [e for e in entries if not e.is_special][0]
        self.assertTrue(regular.membership_paused)
        self.assertEqual(regular.membership_paused_until, pause.requested_end_date)

    def test_checkin_allowed_when_no_active_pause(self):
        checkin, created = perform_checkin(self.person, self.schedule.pk)
        self.assertTrue(created)

    def test_checkin_allowed_after_approved_pause_end(self):
        pause = self._approve_pause_covering_today()
        first_unlocked_date = pause.requested_end_date + timedelta(days=1)

        with (
            patch(
                "system.services.membership.timezone.localdate",
                return_value=first_unlocked_date,
            ),
            patch(
                "system.services.class_calendar.timezone.localdate",
                return_value=first_unlocked_date,
            ),
        ):
            checkin, created = perform_checkin(self.person, self.schedule.pk)

        self.assertTrue(created)
        self.assertEqual(checkin.session.date, first_unlocked_date)


class MembershipPauseRequestCreateViewTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.tier = PlanTier.objects.create(
            code="adult-2x-pause-view-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno View Pausa", cpf="153.509.460-56",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10), current_period_end=now + timedelta(days=20),
            activated_at=now - timedelta(days=100),
        )

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_create_pause_request_via_view(self):
        self._login()
        start = (timezone.localdate() + timedelta(days=1)).strftime("%Y-%m-%d")
        end = (timezone.localdate() + timedelta(days=5)).strftime("%Y-%m-%d")
        response = self.client.post(
            reverse("system:membership-pause-request-create"),
            data={"kind": "self_service", "start_date": start, "end_date": end, "reason_note": ""},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(MembershipPauseRequest.objects.filter(membership=self.membership).count(), 1)

    def test_create_pause_request_without_active_membership_fails(self):
        self.membership.status = MembershipStatus.CANCELED
        self.membership.save()
        self._login()
        start = (timezone.localdate() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = self.client.post(
            reverse("system:membership-pause-request-create"),
            data={"kind": "self_service", "start_date": start, "end_date": start},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])


class MembershipPauseAdminQueueTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code=PersonTypeCode.STUDENT, display_name="Aluno")
        self.admin_type = PersonType.objects.create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT, display_name="Administrativo",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-pause-admin-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier, payment_method=PlanPaymentMethod.PIX, gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY, base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Admin Fila", cpf="283.958.686-00",
            person_type=self.student_type, birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person, plan_price=self.price, status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=10), current_period_end=now + timedelta(days=20),
            activated_at=now - timedelta(days=100),
        )
        start = timezone.localdate() + timedelta(days=1)
        self.pause = create_pause_request(
            self.membership, kind=MembershipPauseRequestKind.MEDICAL,
            start_date=start, end_date=start + timedelta(days=9), reason_note="Atestado teste",
        )

        from system.constants import PortalCapability
        from system.models import OperationalRole, PersonOperationalRole

        self.admin_person = Person.objects.create(
            full_name="Administrativo Fila Pausa", cpf="920.000.011-81",
            person_type=self.admin_type, birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        role = OperationalRole.objects.create(
            code="manage-people-pause-test", display_name="Gestão de pessoas",
            capabilities=[PortalCapability.MANAGE_PEOPLE],
        )
        PersonOperationalRole.objects.create(person=self.admin_person, role=role, is_active=True)
        self.admin_account = PortalAccount(person=self.admin_person)
        self.admin_account.set_password("123456")
        self.admin_account.save()

    def _login_admin(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.admin_account.pk
        session.save()

    def test_queue_lists_pending_request(self):
        self._login_admin()
        response = self.client.get(reverse("system:membership-pause-request-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aluno Admin Fila")

    def test_approve_via_detail_view(self):
        self._login_admin()
        response = self.client.post(
            reverse("system:membership-pause-request-detail", kwargs={"pk": self.pause.pk}),
            data={"action": "approve", "decision_notes": "Confirmado atestado."},
        )
        self.assertEqual(response.status_code, 302)
        self.pause.refresh_from_db()
        self.assertEqual(self.pause.status, MembershipPauseRequestStatus.APPROVED)

    def test_reject_via_detail_view_requires_notes(self):
        self._login_admin()
        response = self.client.post(
            reverse("system:membership-pause-request-detail", kwargs={"pk": self.pause.pk}),
            data={"action": "reject", "decision_notes": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.pause.refresh_from_db()
        self.assertEqual(self.pause.status, MembershipPauseRequestStatus.PENDING)
