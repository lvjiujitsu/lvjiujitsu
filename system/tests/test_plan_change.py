from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from system.models import (
    Membership,
    MembershipCredit,
    MembershipCreditStatus,
    MembershipStatus,
    PaymentProvider,
    PaymentStatus,
    Person,
    PersonType,
    RegistrationOrder,
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    calculate_plan_change,
    create_plan_change_order,
    refund_plan_change_leftover,
)


class CalculatePlanChangeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student_type = PersonType.objects.create(
            code="student",
            display_name="Aluno",
        )
        cls.person = Person.objects.create(
            full_name="Aluno Teste",
            cpf="123.456.789-00",
            email="aluno@example.com",
            person_type=cls.student_type,
            birth_date=date(1990, 1, 1),
        )
        cls.annual_plan = SubscriptionPlan.objects.create(
            code="anual-pix-individual",
            display_name="Plano Anual PIX",
            price=Decimal("3204.00"),
            billing_cycle=BillingCycle.ANNUAL,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
            is_family_plan=False,
        )
        cls.monthly_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-individual",
            display_name="Plano Mensal PIX",
            price=Decimal("267.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
            is_family_plan=False,
        )
        cls.quarterly_plan = SubscriptionPlan.objects.create(
            code="trimestral-pix-individual",
            display_name="Plano Trimestral PIX",
            price=Decimal("720.00"),
            billing_cycle=BillingCycle.QUARTERLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
            is_family_plan=False,
        )

    def _build_membership(self, plan, *, days_used=121, cycle_days=365):
        now = timezone.now()
        return Membership.objects.create(
            person=self.person,
            plan=plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=days_used),
            current_period_end=now + timedelta(days=cycle_days - days_used),
        )

    def _create_paid_order(self, plan, total, *, provider=PaymentProvider.STRIPE):
        return RegistrationOrder.objects.create(
            person=self.person,
            plan=plan,
            plan_price=total,
            total=total,
            payment_status=PaymentStatus.PAID,
            payment_provider=provider,
            stripe_payment_intent_id=(
                "pi_test_main" if provider == PaymentProvider.STRIPE else ""
            ),
            asaas_payment_id="pay_test" if provider == PaymentProvider.ASAAS else "",
            paid_at=timezone.now() - timedelta(days=120),
        )

    def test_annual_to_monthly_creates_extension_with_leftover(self):
        membership = self._build_membership(self.annual_plan, days_used=121, cycle_days=365)
        self._create_paid_order(self.annual_plan, Decimal("3204.00"))

        result = calculate_plan_change(membership, self.monthly_plan)

        self.assertFalse(result["is_upgrade"])
        self.assertTrue(result["is_extension"])
        self.assertGreaterEqual(result["cycles_covered"], 7)
        self.assertEqual(result["additional_charge"], Decimal("0.00"))
        self.assertGreater(result["leftover_credit"], Decimal("0.00"))

    def test_annual_to_quarterly_covers_three_cycles(self):
        membership = self._build_membership(self.annual_plan, days_used=121, cycle_days=365)
        self._create_paid_order(self.annual_plan, Decimal("3204.00"))

        result = calculate_plan_change(membership, self.quarterly_plan)

        self.assertFalse(result["is_upgrade"])
        self.assertEqual(result["cycles_covered"], 2)
        self.assertEqual(result["extension_months"], 6)

    def test_monthly_to_annual_charges_difference_with_full_cycle(self):
        membership = self._build_membership(self.monthly_plan, days_used=10, cycle_days=30)
        self._create_paid_order(self.monthly_plan, Decimal("267.00"))

        result = calculate_plan_change(membership, self.annual_plan)

        self.assertTrue(result["is_upgrade"])
        self.assertFalse(result["is_extension"])
        self.assertEqual(result["cycles_covered"], 1)
        self.assertGreater(result["additional_charge"], Decimal("0.00"))
        self.assertEqual(result["leftover_credit"], Decimal("0.00"))

    def test_calculate_uses_plan_price_when_no_paid_order(self):
        membership = self._build_membership(self.annual_plan, days_used=121, cycle_days=365)

        result = calculate_plan_change(membership, self.monthly_plan)

        self.assertEqual(result["amount_paid"], Decimal("3204.00"))

    def test_inactive_membership_raises(self):
        membership = self._build_membership(self.annual_plan)
        membership.status = MembershipStatus.CANCELED
        membership.save()
        with self.assertRaises(PlanChangeError):
            calculate_plan_change(membership, self.monthly_plan)

    def test_same_plan_raises(self):
        membership = self._build_membership(self.annual_plan)
        with self.assertRaises(PlanChangeError):
            calculate_plan_change(membership, self.annual_plan)


class ApplyPlanChangeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student_type = PersonType.objects.create(
            code="student",
            display_name="Aluno",
        )
        cls.person = Person.objects.create(
            full_name="Aluno Teste",
            cpf="123.456.789-00",
            email="aluno@example.com",
            person_type=cls.student_type,
            birth_date=date(1990, 1, 1),
        )
        cls.annual_plan = SubscriptionPlan.objects.create(
            code="anual",
            display_name="Plano Anual",
            price=Decimal("3204.00"),
            billing_cycle=BillingCycle.ANNUAL,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
        )
        cls.monthly_plan = SubscriptionPlan.objects.create(
            code="mensal",
            display_name="Plano Mensal",
            price=Decimal("267.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
        )

    def _build_membership(self):
        now = timezone.now()
        return Membership.objects.create(
            person=self.person,
            plan=self.annual_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=121),
            current_period_end=now + timedelta(days=244),
        )

    def test_apply_extension_creates_membership_credit_when_leftover(self):
        membership = self._build_membership()
        RegistrationOrder.objects.create(
            person=self.person,
            plan=self.annual_plan,
            plan_price=Decimal("3204.00"),
            total=Decimal("3204.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.STRIPE,
            stripe_payment_intent_id="pi_test",
            paid_at=timezone.now() - timedelta(days=120),
        )
        proration = calculate_plan_change(membership, self.monthly_plan)

        apply_plan_change(None, membership, self.monthly_plan, proration=proration)

        membership.refresh_from_db()
        self.assertEqual(membership.plan_id, self.monthly_plan.pk)
        self.assertEqual(MembershipCredit.objects.filter(membership=membership).count(), 1)
        credit = MembershipCredit.objects.get(membership=membership)
        self.assertEqual(credit.status, MembershipCreditStatus.AVAILABLE)
        self.assertEqual(credit.amount, proration["leftover_credit"])

    def test_apply_with_paid_order_uses_full_cycle(self):
        membership = self._build_membership()
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.monthly_plan,
            plan_price=Decimal("60.00"),
            total=Decimal("60.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.STRIPE,
            is_plan_change=True,
            paid_at=timezone.now(),
        )

        apply_plan_change(order, membership, self.monthly_plan)

        membership.refresh_from_db()
        self.assertEqual(membership.plan_id, self.monthly_plan.pk)
        self.assertEqual(MembershipCredit.objects.filter(membership=membership).count(), 0)


class RefundLeftoverTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student_type = PersonType.objects.create(
            code="student",
            display_name="Aluno",
        )
        cls.person = Person.objects.create(
            full_name="Aluno Teste",
            cpf="123.456.789-00",
            email="aluno@example.com",
            person_type=cls.student_type,
            birth_date=date(1990, 1, 1),
        )
        cls.plan = SubscriptionPlan.objects.create(
            code="plano",
            display_name="Plano",
            price=Decimal("240.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
        )

    def _membership(self):
        now = timezone.now()
        return Membership.objects.create(
            person=self.person,
            plan=self.plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=5),
            current_period_end=now + timedelta(days=25),
        )

    def test_refund_uses_stripe_when_provider_is_stripe(self):
        membership = self._membership()
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("240.00"),
            total=Decimal("240.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.STRIPE,
            stripe_payment_intent_id="pi_real_42",
            paid_at=timezone.now() - timedelta(days=4),
        )
        with patch(
            "system.services.plan_change.refund_order"
        ) as mock_refund:
            mock_refund.return_value = {
                "refund_id": "re_42",
                "amount": Decimal("12.00"),
                "order": order,
            }
            credit = refund_plan_change_leftover(
                membership, Decimal("12.00")
            )
        mock_refund.assert_called_once()
        self.assertEqual(credit.status, MembershipCreditStatus.REFUNDED)
        self.assertEqual(credit.refund_provider, "stripe")
        self.assertEqual(credit.refund_provider_reference, "re_42")

    def test_refund_uses_asaas_when_provider_is_asaas(self):
        membership = self._membership()
        RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("240.00"),
            total=Decimal("240.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.ASAAS,
            asaas_payment_id="pay_real_42",
            paid_at=timezone.now() - timedelta(days=4),
        )
        with patch(
            "system.services.plan_change.refund_payment"
        ) as mock_refund:
            mock_refund.return_value = {"id": "ref_pay_42"}
            credit = refund_plan_change_leftover(
                membership, Decimal("12.00")
            )
        mock_refund.assert_called_once()
        self.assertEqual(credit.refund_provider, "asaas")
        self.assertEqual(credit.refund_provider_reference, "ref_pay_42")

    def test_refund_raises_when_no_paid_order(self):
        membership = self._membership()
        with self.assertRaises(PlanChangeError):
            refund_plan_change_leftover(membership, Decimal("12.00"))

    def test_refund_raises_when_provider_is_manual(self):
        membership = self._membership()
        RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("240.00"),
            total=Decimal("240.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.MANUAL,
            paid_at=timezone.now(),
        )
        with self.assertRaises(PlanChangeError):
            refund_plan_change_leftover(membership, Decimal("12.00"))


class CreatePlanChangeOrderTest(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code="student",
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Aluno Teste",
            cpf="123.456.789-00",
            email="aluno@example.com",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
        )
        self.current_plan = SubscriptionPlan.objects.create(
            code="atual",
            display_name="Plano Atual",
            price=Decimal("240.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
        )
        self.target_plan = SubscriptionPlan.objects.create(
            code="alvo",
            display_name="Plano Alvo",
            price=Decimal("3204.00"),
            billing_cycle=BillingCycle.ANNUAL,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            is_active=True,
        )

    def test_creates_order_only_when_additional_charge_positive(self):
        proration = {
            "current_plan": self.current_plan,
            "available_credit": Decimal("100.00"),
            "additional_charge": Decimal("3104.00"),
        }
        order = create_plan_change_order(
            self.person, None, self.target_plan, proration
        )
        self.assertIsNotNone(order)
        self.assertEqual(order.total, Decimal("3104.00"))
        self.assertTrue(order.is_plan_change)

    def test_returns_none_when_no_charge(self):
        proration = {
            "current_plan": self.current_plan,
            "available_credit": Decimal("3204.00"),
            "additional_charge": Decimal("0.00"),
        }
        order = create_plan_change_order(
            self.person, None, self.target_plan, proration
        )
        self.assertIsNone(order)
