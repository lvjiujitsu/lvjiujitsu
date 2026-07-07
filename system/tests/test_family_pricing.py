from datetime import date
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
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.family_pricing import recompute_family_discounts_for_person
from system.services.stripe_discounts import (
    StripeDiscountError,
    apply_family_discount,
    remove_family_discount,
)


class FamilyPricingRecomputeTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-family-pricing",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.other_tier = PlanTier.objects.create(
            code="adult-5x-family-pricing",
            display_name="Adulto 5x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.other_price = PlanPrice.objects.create(
            tier=self.other_tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("260.00"),
        )
        self.owner = Person.objects.create(
            full_name="Titular Family Pricing",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Family Pricing",
            cpf="153.509.460-56",
            person_type=self.person_type,
            birth_date=date(2010, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def _create_membership(self, person, price, **overrides):
        defaults = {
            "person": person,
            "plan_price": price,
            "status": MembershipStatus.ACTIVE,
            "current_period_start": timezone.now(),
            "current_period_end": timezone.now() + timezone.timedelta(days=30),
        }
        defaults.update(overrides)
        return Membership.objects.create(**defaults)

    def test_single_person_no_discount(self):
        membership = self._create_membership(self.owner, self.price)

        recompute_family_discounts_for_person(self.owner)

        membership.refresh_from_db()
        self.assertFalse(membership.family_discount_applied)
        self.assertEqual(membership.billed_price, self.price.price)

    def test_two_people_same_tier_get_discount(self):
        owner_membership = self._create_membership(self.owner, self.price)
        dependent_membership = self._create_membership(self.dependent, self.price)
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

        recompute_family_discounts_for_person(self.owner)

        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertTrue(owner_membership.family_discount_applied)
        self.assertTrue(dependent_membership.family_discount_applied)
        self.assertEqual(owner_membership.billed_price, self.price.family_price())
        self.assertEqual(dependent_membership.billed_price, self.price.family_price())

    def test_two_people_different_tiers_no_discount(self):
        owner_membership = self._create_membership(self.owner, self.price)
        dependent_membership = self._create_membership(self.dependent, self.other_price)
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

        recompute_family_discounts_for_person(self.owner)

        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertFalse(owner_membership.family_discount_applied)
        self.assertFalse(dependent_membership.family_discount_applied)

    def test_removing_relationship_reverts_discount(self):
        owner_membership = self._create_membership(self.owner, self.price)
        dependent_membership = self._create_membership(self.dependent, self.price)
        relationship = PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        recompute_family_discounts_for_person(self.owner)
        owner_membership.refresh_from_db()
        self.assertTrue(owner_membership.family_discount_applied)

        relationship.delete()
        recompute_family_discounts_for_person(self.owner)
        recompute_family_discounts_for_person(self.dependent)

        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertFalse(owner_membership.family_discount_applied)
        self.assertFalse(dependent_membership.family_discount_applied)
        self.assertEqual(owner_membership.billed_price, self.price.price)
        self.assertEqual(dependent_membership.billed_price, self.price.price)

    @patch("system.services.family_pricing.apply_family_discount")
    def test_stripe_discount_applied_only_on_change(self, mocked_apply):
        self._create_membership(
            self.owner, self.price, stripe_subscription_id="sub_owner_1"
        )
        self._create_membership(
            self.dependent, self.price, stripe_subscription_id="sub_owner_1"
        )
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

        recompute_family_discounts_for_person(self.owner)
        self.assertEqual(mocked_apply.call_count, 2)

        mocked_apply.reset_mock()
        recompute_family_discounts_for_person(self.owner)
        mocked_apply.assert_not_called()


class LegacyPlanTierInteropTestCase(TestCase):
    """Titular ainda em SubscriptionPlan legado (Individual) + dependente já no
    novo PlanPrice devem ser reconhecidos como o mesmo tier comercial (audience +
    weekly_frequency), sem exigir migração do Membership do titular."""

    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-legacy-interop",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.legacy_plan = SubscriptionPlan.objects.create(
            code="legacy-individual-2x-interop",
            display_name="Individual 2x por semana (legado)",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            is_family_plan=False,
            is_loyalty_plan=False,
            price=Decimal("220.00"),
        )
        self.loyalty_plan = SubscriptionPlan.objects.create(
            code="legacy-loyalty-2x-interop",
            display_name="Veterano 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            is_family_plan=False,
            is_loyalty_plan=True,
            price=Decimal("203.01"),
        )
        self.owner = Person.objects.create(
            full_name="Titular Legado Interop",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Novo Interop",
            cpf="153.509.460-56",
            person_type=self.person_type,
            birth_date=date(2010, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

    def test_legacy_owner_and_new_dependent_share_matched_tier_discount(self):
        owner_membership = Membership.objects.create(
            person=self.owner,
            plan=self.legacy_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        dependent_membership = Membership.objects.create(
            person=self.dependent,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        recompute_family_discounts_for_person(self.owner)

        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertTrue(owner_membership.family_discount_applied)
        self.assertTrue(dependent_membership.family_discount_applied)
        self.assertEqual(
            owner_membership.billed_price,
            (self.legacy_plan.price * Decimal("0.82")).quantize(Decimal("0.01")),
        )
        self.assertEqual(dependent_membership.billed_price, self.price.family_price())

    def test_loyalty_membership_never_receives_family_discount(self):
        owner_membership = Membership.objects.create(
            person=self.owner,
            plan=self.loyalty_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        Membership.objects.create(
            person=self.dependent,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        recompute_family_discounts_for_person(self.owner)

        owner_membership.refresh_from_db()
        self.assertFalse(owner_membership.family_discount_applied)
        self.assertIsNone(owner_membership.billed_price)


@override_settings(STRIPE_SECRET_KEY="sk_test_dummy")
class StripeFamilyDiscountTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-stripe-discount",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.person = Person.objects.create(
            full_name="Titular Stripe Discount",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_stripe_discount_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

    @patch("system.services.stripe_discounts.stripe.Subscription.modify")
    @patch("system.services.stripe_discounts.stripe.Coupon.retrieve")
    def test_apply_family_discount_reuses_existing_coupon(self, mocked_retrieve, mocked_modify):
        mocked_retrieve.return_value = {"id": "family-discount-1800"}

        apply_family_discount(self.membership)

        mocked_retrieve.assert_called_once_with("family-discount-1800")
        mocked_modify.assert_called_once_with(
            "sub_stripe_discount_1", discounts=[{"coupon": "family-discount-1800"}]
        )

    @patch("system.services.stripe_discounts.stripe.Subscription.modify")
    @patch("system.services.stripe_discounts.stripe.Coupon.create")
    @patch("system.services.stripe_discounts.stripe.Coupon.retrieve")
    def test_apply_family_discount_creates_coupon_when_missing(
        self, mocked_retrieve, mocked_create, mocked_modify
    ):
        mocked_retrieve.side_effect = Exception("no such coupon")
        mocked_create.return_value = {"id": "family-discount-1800"}

        apply_family_discount(self.membership)

        mocked_create.assert_called_once_with(
            id="family-discount-1800", percent_off=18.0, duration="forever"
        )
        mocked_modify.assert_called_once_with(
            "sub_stripe_discount_1", discounts=[{"coupon": "family-discount-1800"}]
        )

    @patch("system.services.stripe_discounts.stripe.Subscription.delete_discount")
    def test_remove_family_discount_calls_delete_discount(self, mocked_delete):
        remove_family_discount(self.membership)

        mocked_delete.assert_called_once_with("sub_stripe_discount_1")

    def test_apply_family_discount_without_subscription_id_is_noop(self):
        self.membership.stripe_subscription_id = ""
        self.membership.save(update_fields=["stripe_subscription_id"])

        result = apply_family_discount(self.membership)

        self.assertIsNone(result)

    @override_settings(STRIPE_SECRET_KEY="")
    def test_apply_family_discount_without_secret_key_raises(self):
        with self.assertRaises(StripeDiscountError):
            apply_family_discount(self.membership)


class DependentRemoveViewFamilyPricingTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-remove-view",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.owner = Person.objects.create(
            full_name="Titular Remove View",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Remove View",
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
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        recompute_family_discounts_for_person(self.owner)

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_removing_dependent_reverts_billed_price_for_both(self):
        self.owner_membership.refresh_from_db()
        self.assertTrue(self.owner_membership.family_discount_applied)
        self._login()

        response = self.client.post(
            reverse("system:dependent-remove", args=[self.dependent.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.owner_membership.refresh_from_db()
        self.dependent_membership.refresh_from_db()
        self.assertFalse(self.owner_membership.family_discount_applied)
        self.assertFalse(self.dependent_membership.family_discount_applied)
        self.assertEqual(self.owner_membership.billed_price, self.price.price)
        self.assertEqual(self.dependent_membership.billed_price, self.price.price)


class AdminCancellationFamilyPricingTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-admin-cancel",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.owner = Person.objects.create(
            full_name="Titular Admin Cancel",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Admin Cancel",
            cpf="153.509.460-56",
            person_type=self.person_type,
            birth_date=date(2010, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
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
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        recompute_family_discounts_for_person(self.owner)
        self.owner_membership.refresh_from_db()
        self.assertTrue(self.owner_membership.family_discount_applied)

    def test_cancel_membership_without_stripe_subscription_reverts_remaining_discount(self):
        from system.services.stripe_admin_actions import cancel_membership

        cancel_membership(self.dependent_membership, at_period_end=False)

        self.owner_membership.refresh_from_db()
        self.assertFalse(self.owner_membership.family_discount_applied)
        self.assertEqual(self.owner_membership.billed_price, self.price.price)

    @patch("system.services.stripe_admin_actions.stripe.Subscription.delete")
    @override_settings(STRIPE_SECRET_KEY="sk_test_dummy")
    def test_cancel_membership_immediate_stripe_reverts_remaining_discount(self, mocked_delete):
        self.dependent_membership.stripe_subscription_id = "sub_admin_cancel_1"
        self.dependent_membership.save(update_fields=["stripe_subscription_id"])

        from system.services.stripe_admin_actions import cancel_membership

        cancel_membership(self.dependent_membership, at_period_end=False)

        self.owner_membership.refresh_from_db()
        self.assertFalse(self.owner_membership.family_discount_applied)
        self.assertEqual(self.owner_membership.billed_price, self.price.price)

    @patch("system.services.stripe_admin_actions.stripe.Subscription.modify")
    @override_settings(STRIPE_SECRET_KEY="sk_test_dummy")
    def test_cancel_membership_at_period_end_does_not_revert_yet(self, mocked_modify):
        self.dependent_membership.stripe_subscription_id = "sub_admin_cancel_2"
        self.dependent_membership.save(update_fields=["stripe_subscription_id"])

        from system.services.stripe_admin_actions import cancel_membership

        cancel_membership(self.dependent_membership, at_period_end=True)

        self.owner_membership.refresh_from_db()
        self.assertTrue(self.owner_membership.family_discount_applied)

    def test_mark_membership_canceled_reverts_remaining_discount(self):
        from system.services.membership import mark_membership_canceled

        self.dependent_membership.stripe_subscription_id = "sub_webhook_cancel_1"
        self.dependent_membership.save(update_fields=["stripe_subscription_id"])

        mark_membership_canceled({"id": "sub_webhook_cancel_1", "canceled_at": None})

        self.owner_membership.refresh_from_db()
        self.assertFalse(self.owner_membership.family_discount_applied)
        self.assertEqual(self.owner_membership.billed_price, self.price.price)
