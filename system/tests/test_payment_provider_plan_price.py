from decimal import Decimal

from django.test import TestCase

from system.models import Person, PersonType, RegistrationOrder
from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanPrice,
    PlanTier,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)
from system.models.registration_order import PaymentProvider
from system.services.financial_transactions import (
    apply_order_financials,
    resolve_payment_provider_for_plan,
)
from system.services.membership import activate_membership_from_session
from system.services.registration_checkout import (
    CATALOG_ID_PREFIX_PLAN_PRICE,
    build_catalog_plan_id,
    create_registration_order,
)


class PaymentProviderPlanPriceTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.person = Person.objects.create(
            full_name="Aluno Provider",
            cpf="111.222.333-55",
            person_type=self.person_type,
        )
        self.stripe_tier = PlanTier.objects.create(
            code="adult-2x-provider",
            display_name="Adulto 2x",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.stripe_price = PlanPrice.objects.create(
            tier=self.stripe_tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("220.00"),
        )
        self.pix_plan = SubscriptionPlan.objects.create(
            code="pix-provider",
            display_name="PIX legado",
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            price=Decimal("200.00"),
        )

    def test_stripe_plan_price_resolves_to_stripe_provider(self):
        self.assertEqual(
            resolve_payment_provider_for_plan(self.stripe_price),
            PaymentProvider.STRIPE,
        )

    def test_order_with_only_plan_price_ref_gets_stripe_financials(self):
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan_price_ref=self.stripe_price,
            plan_price=Decimal("230.37"),
            total=Decimal("230.37"),
        )

        apply_order_financials(order)
        order.refresh_from_db()

        self.assertEqual(order.payment_provider, PaymentProvider.STRIPE)
        self.assertGreater(order.administrative_fee, Decimal("0"))
        self.assertGreater(order.net_amount, Decimal("0"))

    def test_create_registration_order_with_plan_price_sets_stripe_provider(self):
        cleaned_data = {
            "selected_plan": build_catalog_plan_id(
                CATALOG_ID_PREFIX_PLAN_PRICE, self.stripe_price.pk
            ),
            "registration_profile": "holder",
        }
        order = create_registration_order(self.person, cleaned_data)
        order.refresh_from_db()

        self.assertIsNotNone(order)
        self.assertIsNone(order.plan_id)
        self.assertEqual(order.plan_price_ref_id, self.stripe_price.pk)
        self.assertEqual(order.payment_provider, PaymentProvider.STRIPE)

    def test_activate_membership_from_session_accepts_plan_price_only_order(self):
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan_price_ref=self.stripe_price,
            plan_price=Decimal("230.37"),
            total=Decimal("230.37"),
            payment_provider=PaymentProvider.STRIPE,
        )
        stripe_session = {
            "subscription": "sub_plan_price_only",
            "customer": "cus_plan_price_only",
        }

        membership = activate_membership_from_session(order, stripe_session)

        self.assertIsNotNone(membership)
        self.assertIsNone(membership.plan_id)
        self.assertEqual(membership.plan_price_id, self.stripe_price.pk)
        self.assertEqual(membership.stripe_subscription_id, "sub_plan_price_only")
