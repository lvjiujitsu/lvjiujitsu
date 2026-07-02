from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Person, PersonType
from system.models.membership import Membership, MembershipStatus
from system.models.plan import SubscriptionPlan
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class MembershipActionsUiTestCase(TestCase):
    """PRD-103: acoes de assinatura no detalhe de pessoa."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-membership-actions",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.student = Person.objects.create(
            full_name="Aluno Fundacao Assinatura",
            cpf="111.222.333-44",
            person_type=self.student_type,
            birth_date=date(1995, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="plan-membership-actions-fundacao",
            display_name="Plano Fundacao Assinatura",
            price="200.00",
        )
        self.other_plan = SubscriptionPlan.objects.create(
            code="plan-membership-actions-fundacao-2",
            display_name="Plano Fundacao Assinatura 2",
            price="250.00",
        )
        self._login_technical_admin()

    def test_person_detail_shows_actions_for_active_membership(self):
        Membership.objects.create(
            person=self.student,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
        )
        response = self.client.get(
            reverse("system:person-detail", kwargs={"pk": self.student.pk})
        )
        self.assertContains(response, "Trocar plano")
        self.assertContains(response, "Cancelar assinatura")

    def test_person_detail_hides_actions_without_active_membership(self):
        response = self.client.get(
            reverse("system:person-detail", kwargs={"pk": self.student.pk})
        )
        self.assertNotContains(response, "Cancelar assinatura")

    def test_cancel_membership_without_stripe_id_cancels_locally(self):
        membership = Membership.objects.create(
            person=self.student,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
        )
        next_url = reverse("system:person-detail", kwargs={"pk": self.student.pk})
        response = self.client.post(
            reverse("system:cancel-membership", kwargs={"membership_id": membership.pk}),
            data={"next": next_url},
        )
        self.assertRedirects(response, next_url)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.CANCELED)

    def test_change_plan_without_stripe_id_shows_error(self):
        membership = Membership.objects.create(
            person=self.student,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
        )
        next_url = reverse("system:person-detail", kwargs={"pk": self.student.pk})
        response = self.client.post(
            reverse("system:change-membership-plan", kwargs={"membership_id": membership.pk}),
            data={"plan_id": self.other_plan.pk, "next": next_url},
        )
        self.assertRedirects(response, next_url)
        membership.refresh_from_db()
        self.assertEqual(membership.plan_id, self.plan.pk)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
