import json
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
    RegistrationOrder,
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod
from system.services import PORTAL_ACCOUNT_SESSION_KEY


class PlanChangeSelectViewTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Aluno Troca de Plano",
            cpf="353.769.401-60",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
        )
        self.account = PortalAccount.objects.create(person=self.person, password_hash="hash")
        self.current_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-individual-view-test",
            display_name="Plano Mensal PIX",
            price=Decimal("267.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_active=True,
        )
        self.cheaper_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-individual-cheaper-view-test",
            display_name="Plano Mensal PIX Econômico",
            price=Decimal("50.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_active=True,
        )
        self.pricier_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-individual-pricier-view-test",
            display_name="Plano Mensal PIX Premium",
            price=Decimal("500.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_active=True,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person,
            plan=self.current_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=15),
            current_period_end=now + timedelta(days=15),
        )
        RegistrationOrder.objects.create(
            person=self.person,
            plan=self.current_plan,
            plan_price=self.current_plan.price,
            total=self.current_plan.price,
            payment_status="paid",
            paid_at=now - timedelta(days=15),
        )

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_downgrade_applies_immediately_without_checkout(self):
        self._login()

        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": self.cheaper_plan.pk, "leftover_action": "keep_credit"},
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["success"])
        self.assertNotIn("redirect_url", payload)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.plan_id, self.cheaper_plan.pk)

    def test_upgrade_redirects_to_checkout_without_applying_yet(self):
        self._login()

        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": self.pricier_plan.pk},
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["success"])
        self.assertIn("/pagamentos/", payload["redirect_url"])
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.plan_id, self.current_plan.pk)
        order = RegistrationOrder.objects.filter(is_plan_change=True).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.plan_id, self.pricier_plan.pk)

    def test_stripe_recurring_membership_is_rejected(self):
        self.membership.stripe_subscription_id = "sub_test_123"
        self.membership.save(update_fields=["stripe_subscription_id"])
        self._login()

        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": self.cheaper_plan.pk},
        )

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertFalse(payload["success"])
        self.assertIn("assinatura recorrente", payload["error"])
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.plan_id, self.current_plan.pk)

    def test_same_plan_is_rejected(self):
        self._login()

        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": self.current_plan.pk},
        )

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertFalse(payload["success"])

    def test_unauthenticated_is_redirected_to_login(self):
        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": self.cheaper_plan.pk},
        )
        self.assertEqual(response.status_code, 302)


class HomeDashboardPlanChangeContextTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Aluno Home Troca Plano",
            cpf="744.126.528-23",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
        )
        self.account = PortalAccount.objects.create(person=self.person, password_hash="hash")
        self.current_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-individual-home-test",
            display_name="Plano Mensal PIX Home",
            price=Decimal("267.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_active=True,
        )
        SubscriptionPlan.objects.create(
            code="mensal-pix-individual-home-cheaper-test",
            display_name="Plano Mensal PIX Home Econômico",
            price=Decimal("50.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            audience=PlanAudience.ADULT,
            is_active=True,
        )
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person,
            plan=self.current_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=15),
            current_period_end=now + timedelta(days=15),
        )
        RegistrationOrder.objects.create(
            person=self.person,
            plan=self.current_plan,
            plan_price=self.current_plan.price,
            total=self.current_plan.price,
            payment_status="paid",
            paid_at=now - timedelta(days=15),
        )

    def _login(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_home_shows_plan_change_button_for_non_recurring_membership(self):
        self._login(self.account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["plan_change_locked"])
        self.assertTrue(response.context["plan_change_catalog"])
        self.assertContains(response, "js-open-plan-change-modal")

    def test_home_hides_plan_change_button_for_stripe_recurring_membership(self):
        self.membership.stripe_subscription_id = "sub_test_456"
        self.membership.save(update_fields=["stripe_subscription_id"])
        self._login(self.account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["plan_change_locked"])
        self.assertFalse(response.context["plan_change_catalog"])
        self.assertNotContains(response, "js-open-plan-change-modal")
