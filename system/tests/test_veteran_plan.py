from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PortalAccount,
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod
from system.selectors.plan_eligibility import (
    PlanEligibilityContext,
    compute_veteran_member_since,
    get_eligible_plans,
    is_plan_eligible,
    is_veteran_plan_eligible,
)
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.veteran_plan import approve_veteran_plan, revoke_veteran_plan


def _make_plan(code, *, is_loyalty_plan=False):
    return SubscriptionPlan.objects.create(
        code=code,
        display_name=code,
        price=Decimal("100.00"),
        billing_cycle=BillingCycle.MONTHLY,
        payment_method=PlanPaymentMethod.PIX,
        audience=PlanAudience.ADULT,
        is_loyalty_plan=is_loyalty_plan,
        is_active=True,
    )


class VeteranTenureCalculationTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.plan = _make_plan("mensal-pix-individual-veteran-test")

    def _make_person(self, cpf):
        return Person.objects.create(
            full_name="Aluno Veterano Teste",
            cpf=cpf,
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
        )

    def test_new_person_without_membership_is_not_veteran_eligible(self):
        person = self._make_person("391.539.028-31")
        self.assertIsNone(compute_veteran_member_since(person))
        self.assertFalse(is_veteran_plan_eligible(person))

    def test_two_consecutive_years_grants_veteran_eligibility(self):
        person = self._make_person("884.918.551-06")
        reference = timezone.now()
        activated_at = reference - timedelta(days=800)
        Membership.objects.create(
            person=person,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            activated_at=activated_at,
            current_period_start=activated_at,
            current_period_end=reference + timedelta(days=15),
        )
        self.assertEqual(
            compute_veteran_member_since(person, reference_date=reference),
            activated_at,
        )
        self.assertTrue(is_veteran_plan_eligible(person, reference_date=reference))

    def test_tenure_below_two_years_is_not_eligible(self):
        person = self._make_person("176.198.458-60")
        reference = timezone.now()
        activated_at = reference - timedelta(days=200)
        Membership.objects.create(
            person=person,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            activated_at=activated_at,
            current_period_start=activated_at,
            current_period_end=reference + timedelta(days=15),
        )
        self.assertFalse(is_veteran_plan_eligible(person, reference_date=reference))

    def test_gap_beyond_grace_period_resets_member_since(self):
        person = self._make_person("697.373.594-02")
        reference = timezone.now()
        old_start = reference - timedelta(days=900)
        old_end = reference - timedelta(days=400)
        Membership.objects.create(
            person=person,
            plan=self.plan,
            status=MembershipStatus.CANCELED,
            activated_at=old_start,
            current_period_start=old_start,
            current_period_end=old_start + timedelta(days=30),
            canceled_at=old_end,
        )
        new_start = reference - timedelta(days=100)
        Membership.objects.create(
            person=person,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            activated_at=new_start,
            current_period_start=new_start,
            current_period_end=reference + timedelta(days=15),
        )
        self.assertEqual(
            compute_veteran_member_since(person, reference_date=reference),
            new_start,
        )
        self.assertFalse(is_veteran_plan_eligible(person, reference_date=reference))

    def test_gap_within_grace_period_does_not_reset_member_since(self):
        person = self._make_person("112.945.283-27")
        reference = timezone.now()
        old_start = reference - timedelta(days=800)
        old_end = reference - timedelta(days=750)
        Membership.objects.create(
            person=person,
            plan=self.plan,
            status=MembershipStatus.CANCELED,
            activated_at=old_start,
            current_period_start=old_start,
            current_period_end=old_start + timedelta(days=30),
            canceled_at=old_end,
        )
        new_start = reference - timedelta(days=730)
        Membership.objects.create(
            person=person,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            activated_at=new_start,
            current_period_start=new_start,
            current_period_end=reference + timedelta(days=15),
        )
        self.assertEqual(
            compute_veteran_member_since(person, reference_date=reference),
            old_start,
        )
        self.assertTrue(is_veteran_plan_eligible(person, reference_date=reference))


class VeteranManualApprovalTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Aluno Aprovação Manual",
            cpf="751.821.450-47",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
        )

    def test_manual_approval_grants_eligibility_regardless_of_tenure(self):
        self.assertFalse(is_veteran_plan_eligible(self.person))
        approve_veteran_plan(self.person, approved_by=None, notes="Retorno consistente.")
        self.person.refresh_from_db()
        self.assertTrue(self.person.veteran_plan_approved)
        self.assertEqual(self.person.veteran_plan_approved_notes, "Retorno consistente.")
        self.assertTrue(is_veteran_plan_eligible(self.person))

    def test_manual_revocation_removes_eligibility(self):
        approve_veteran_plan(self.person, approved_by=None)
        revoke_veteran_plan(self.person, revoked_by=None, notes="Interrompeu o vínculo.")
        self.person.refresh_from_db()
        self.assertFalse(self.person.veteran_plan_approved)
        self.assertFalse(is_veteran_plan_eligible(self.person))


class VeteranPlanCatalogFilterTestCase(TestCase):
    def setUp(self):
        self.veteran_plan = _make_plan(
            "mensal-pix-individual-veteran-catalog-test", is_loyalty_plan=True
        )
        self.regular_plan = _make_plan("mensal-pix-individual-regular-catalog-test")

    def test_veteran_plan_excluded_from_catalog_when_not_eligible(self):
        context = PlanEligibilityContext(
            adult_active=True,
            kids_juvenile_active_count=0,
            veteran_eligible=False,
        )
        self.assertFalse(is_plan_eligible(self.veteran_plan, context))
        catalog = get_eligible_plans(context)
        self.assertNotIn(self.veteran_plan, list(catalog))
        self.assertIn(self.regular_plan, list(catalog))

    def test_veteran_plan_included_in_catalog_when_eligible(self):
        context = PlanEligibilityContext(
            adult_active=True,
            kids_juvenile_active_count=0,
            veteran_eligible=True,
        )
        self.assertTrue(is_plan_eligible(self.veteran_plan, context))
        catalog = get_eligible_plans(context)
        self.assertIn(self.veteran_plan, list(catalog))


class VeteranPlanDecisionViewPermissionTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.admin_type = PersonType.objects.create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            display_name="Administrativo",
        )
        self.manager = Person.objects.create(
            full_name="Gestora de Pessoas",
            cpf="361.451.333-50",
            person_type=self.admin_type,
            birth_date=date(1985, 1, 1),
        )
        self.manager_account = PortalAccount.objects.create(
            person=self.manager, password_hash="hash"
        )
        self.student = Person.objects.create(
            full_name="Aluno Comum Veterano",
            cpf="712.976.551-84",
            person_type=self.student_type,
            birth_date=date(1997, 1, 1),
        )
        self.student_account = PortalAccount.objects.create(
            person=self.student, password_hash="hash"
        )

    def _login(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_manager_can_approve_veteran_plan(self):
        self._login(self.manager_account)

        response = self.client.post(
            reverse("system:person-veteran-plan-decision", kwargs={"pk": self.student.pk}),
            data={"action": "approve", "notes": "Aprovado em teste."},
        )

        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.veteran_plan_approved)
        self.assertEqual(self.student.veteran_plan_approved_by_id, self.manager.pk)

    def test_regular_student_cannot_approve_veteran_plan(self):
        self._login(self.student_account)

        response = self.client.post(
            reverse("system:person-veteran-plan-decision", kwargs={"pk": self.student.pk}),
            data={"action": "approve"},
        )

        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertFalse(self.student.veteran_plan_approved)
