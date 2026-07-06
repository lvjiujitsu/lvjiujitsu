from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Membership, MembershipStatus, Person, PersonType, SubscriptionPlan
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod
from system.services.stripe_checkout import (
    StripeCheckoutError,
    merge_plan_into_existing_subscription,
)


@override_settings(STRIPE_SECRET_KEY="sk_test_dummy")
class MergePlanIntoExistingSubscriptionTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.owner = Person.objects.create(
            full_name="Titular Merge Subscription",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="plan-merge-subscription",
            display_name="Plano Merge Subscription",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("120.00"),
            gateway_code="stripe_card",
            stripe_price_id="price_merge_subscription",
        )

    @patch("system.services.stripe_checkout.stripe.SubscriptionItem.create")
    def test_merge_creates_subscription_item_on_owner_subscription(self, mocked_create):
        mocked_create.return_value = {"id": "si_created_1"}
        membership = Membership.objects.create(
            person=self.owner,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_owner_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        result = merge_plan_into_existing_subscription(membership, self.plan)

        mocked_create.assert_called_once_with(
            subscription="sub_owner_1",
            price="price_merge_subscription",
        )
        self.assertEqual(result["stripe_subscription_id"], "sub_owner_1")
        self.assertEqual(result["stripe_subscription_item_id"], "si_created_1")

    def test_merge_without_owner_subscription_raises(self):
        membership = Membership.objects.create(
            person=self.owner,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        with self.assertRaises(StripeCheckoutError):
            merge_plan_into_existing_subscription(membership, self.plan)

    def test_merge_without_plan_stripe_price_id_raises(self):
        membership = Membership.objects.create(
            person=self.owner,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_owner_2",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        self.plan.stripe_price_id = ""
        self.plan.save(update_fields=["stripe_price_id"])

        with self.assertRaises(StripeCheckoutError):
            merge_plan_into_existing_subscription(membership, self.plan)
