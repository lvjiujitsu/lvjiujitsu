from datetime import date
from decimal import Decimal

from django.test import TestCase
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
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.plan_change import get_plan_change_lock, is_plan_change_locked


class PlanChangeLockRecognizesPlanPriceTestCase(TestCase):

    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-lock-regression",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Pessoa Lock Regression",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def test_locked_when_plan_price_has_stripe_subscription_within_period(self):
        membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_lock_regression_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        self.assertTrue(is_plan_change_locked(membership))
        lock = get_plan_change_lock(membership)
        self.assertTrue(lock["is_locked"])
        self.assertIn("Troca e cancelamento liberados em", lock["message"])

    def test_locked_when_plan_price_gateway_is_stripe_even_without_subscription_id(self):
        membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        self.assertTrue(is_plan_change_locked(membership))

    def test_unlocked_after_current_period_end_in_the_past(self):
        membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_lock_regression_2",
            current_period_start=timezone.now() - timezone.timedelta(days=60),
            current_period_end=timezone.now() - timezone.timedelta(days=1),
        )

        lock = get_plan_change_lock(membership)
        self.assertFalse(lock["is_locked"])

    def test_unlocked_for_non_stripe_plan_price(self):
        pix_price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        membership = Membership.objects.create(
            person=self.person,
            plan_price=pix_price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        self.assertFalse(is_plan_change_locked(membership))


class DependentRemovalCancellationLockTestCase(TestCase):

    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        PersonType.objects.create(
            code=PersonTypeCode.DEPENDENT,
            display_name="Dependente",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-removal-lock",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.owner = Person.objects.create(
            full_name="Titular Removal Lock",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Removal Lock",
            cpf="153.509.460-56",
            person_type=self.person_type,
            birth_date=date(2010, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.account = PortalAccount(person=self.owner)
        self.account.set_password("123456")
        self.account.save()
        self.owner_membership = Membership.objects.create(
            person=self.owner,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        self.dependent_membership = Membership.objects.create(
            person=self.dependent,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_removal_lock_dependent",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        self.relationship = PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_removal_blocked_before_carencia_ends(self):
        self._login()

        response = self.client.post(
            reverse("system:dependent-remove", args=[self.dependent.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PersonRelationship.objects.filter(pk=self.relationship.pk).exists()
        )

    def test_removal_allowed_after_carencia_ends(self):
        self._login()
        self.dependent_membership.current_period_end = timezone.now() - timezone.timedelta(days=1)
        self.dependent_membership.save(update_fields=["current_period_end"])

        response = self.client.post(
            reverse("system:dependent-remove", args=[self.dependent.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            PersonRelationship.objects.filter(pk=self.relationship.pk).exists()
        )

    def test_removal_allowed_when_no_stripe_subscription(self):
        self._login()
        self.dependent_membership.stripe_subscription_id = ""
        self.dependent_membership.plan_price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.dependent_membership.save(update_fields=["stripe_subscription_id", "plan_price"])

        response = self.client.post(
            reverse("system:dependent-remove", args=[self.dependent.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            PersonRelationship.objects.filter(pk=self.relationship.pk).exists()
        )

    def test_removal_allowed_when_dependent_has_no_membership(self):
        self._login()
        self.dependent_membership.delete()

        response = self.client.post(
            reverse("system:dependent-remove", args=[self.dependent.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            PersonRelationship.objects.filter(pk=self.relationship.pk).exists()
        )
