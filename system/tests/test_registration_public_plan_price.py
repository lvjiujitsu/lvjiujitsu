
from decimal import Decimal

from django.test import TestCase

from system.forms.registration_forms import PortalRegistrationForm
from system.models import (
    BiologicalSex,
    Membership,
    PreRegistration,
    PreRegistrationStatus,
    RegistrationOrder,
)
from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanPrice,
    PlanTier,
    PlanWeeklyFrequency,
)
from system.models.registration_order import PaymentStatus
from system.services.pre_registration import finalize_pre_registration
from system.services.registration_checkout import (
    CATALOG_ID_PREFIX_PLAN_PRICE,
    build_catalog_plan_id,
    create_registration_order,
)


def pp_id(plan_price_pk):
    return build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, plan_price_pk)


class PortalRegistrationFormPlanPriceTestCase(TestCase):
    def setUp(self):
        self.adult_tier = PlanTier.objects.create(
            code="adult-2x-public-form",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.adult_price = PlanPrice.objects.create(
            tier=self.adult_tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.kids_tier = PlanTier.objects.create(
            code="kids-2x-public-form",
            display_name="Kids 2x por semana",
            audience=PlanAudience.KIDS_JUVENILE,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.kids_price = PlanPrice.objects.create(
            tier=self.kids_tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("180.00"),
        )

    def _holder_payload(self, **overrides):
        payload = {
            "registration_profile": "holder",
            "holder_name": "Aluno Plan Price Publico",
            "holder_cpf": "52998224725",
            "holder_birthdate": "01/04/1995",
            "holder_biological_sex": BiologicalSex.MALE,
            "holder_password": "123456",
            "holder_password_confirm": "123456",
            "holder_has_martial_art": "no",
            "checkout_action": "pix",
        }
        payload.update(overrides)
        return payload

    def test_adult_holder_can_select_matching_plan_price(self):
        form = PortalRegistrationForm(
            data=self._holder_payload(selected_plan=pp_id(self.adult_price.pk))
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["selected_plan"], pp_id(self.adult_price.pk))

    def test_adult_holder_cannot_select_kids_plan_price(self):
        form = PortalRegistrationForm(
            data=self._holder_payload(selected_plan=pp_id(self.kids_price.pk))
        )

        self.assertFalse(form.is_valid())
        self.assertIn("selected_plan", form.errors)

    def test_invalid_catalog_id_is_rejected(self):
        form = PortalRegistrationForm(
            data=self._holder_payload(selected_plan="pp:999999")
        )

        self.assertFalse(form.is_valid())
        self.assertIn("selected_plan", form.errors)


class CreateRegistrationOrderPlanPriceTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-public-order",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        from datetime import date

        from system.constants import PersonTypeCode
        from system.models import Person, PersonType

        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Aluno Plan Price Order",
            cpf="529.982.247-25",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )

    def test_creates_order_with_plan_price_ref_and_no_legacy_plan(self):
        order = create_registration_order(
            self.person,
            {"selected_plan": pp_id(self.price.pk), "registration_profile": "holder"},
        )

        self.assertIsNotNone(order)
        self.assertIsNone(order.plan_id)
        self.assertEqual(order.plan_price_ref_id, self.price.pk)
        self.assertEqual(order.total, self.price.price)

    def test_multiplies_total_by_training_persons_for_plan_price(self):
        order = create_registration_order(
            self.person,
            {
                "selected_plan": pp_id(self.price.pk),
                "registration_profile": "holder",
                "dependent_name": "Dependente Junto",
            },
        )

        self.assertEqual(order.total, self.price.price * 2)

    def test_returns_none_for_unknown_catalog_id(self):
        order = create_registration_order(
            self.person,
            {"selected_plan": "pp:999999", "registration_profile": "holder"},
        )

        self.assertIsNone(order)


class FinalizePreRegistrationPlanPriceTestCase(TestCase):
    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-public-finalize",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )

    def test_finalize_with_plan_price_creates_membership_referencing_plan_price(self):
        catalog_id = pp_id(self.price.pk)
        pre_registration = PreRegistration.objects.create(
            session_key="plan-price-public-session",
            registration_profile="holder",
            holder_cpf="390.533.447-05",
            holder_email="planprice.publico@example.com",
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "registration_profile": "holder",
                "holder_name": "Aluno Plan Price Finalize",
                "holder_cpf": "390.533.447-05",
                "holder_birthdate": "10/10/1990",
                "holder_biological_sex": "male",
                "holder_email": "planprice.publico@example.com",
                "holder_password": "Teste@12345",
                "holder_password_confirm": "Teste@12345",
                "holder_has_martial_art": "no",
                "checkout_action": "pix",
                "selected_plan": catalog_id,
                "plan_paid": True,
                "plan_payment": {"asaas_payment_id": "pay_public_pp_1"},
            },
        )

        result = finalize_pre_registration(pre_registration)

        self.assertTrue(result["ok"], result.get("error"))
        person = result["person"]
        membership = Membership.objects.get(person=person)
        self.assertEqual(membership.plan_price_id, self.price.pk)
        self.assertIsNone(membership.plan_id)

        order = RegistrationOrder.objects.get(person=person)
        self.assertEqual(order.plan_price_ref_id, self.price.pk)
        self.assertIsNone(order.plan_id)
        self.assertEqual(order.payment_status, PaymentStatus.PAID)
