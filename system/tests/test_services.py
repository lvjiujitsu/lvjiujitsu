from datetime import date
from decimal import Decimal

from django.test import TestCase

from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    Person,
    PersonType,
    RegistrationOrder,
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.models.registration_order import DepositStatus, PaymentProvider
from system.services.financial_transactions import (
    apply_order_financials,
    calculate_financial_amounts,
)
from system.services.registration_checkout import get_registration_plan_multiplier
from system.services.seeding import seed_class_catalog


class FinancialTransactionServiceTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.person = Person.objects.create(
            full_name="Aluno Financeiro",
            cpf="111.222.333-44",
            person_type=self.person_type,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="standard-monthly-pix",
            display_name="Plano mensal PIX",
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            price=Decimal("240.00"),
        )

    def test_calculates_asaas_pix_fixed_fee(self):
        result = calculate_financial_amounts(Decimal("240.00"), PaymentProvider.ASAAS)

        self.assertEqual(result["administrative_fee"], Decimal("1.99"))
        self.assertEqual(result["net_amount"], Decimal("238.01"))

    def test_calculates_stripe_credit_fee(self):
        result = calculate_financial_amounts(Decimal("250.00"), PaymentProvider.STRIPE)

        self.assertEqual(result["administrative_fee"], Decimal("10.37"))
        self.assertEqual(result["net_amount"], Decimal("239.63"))

    def test_apply_order_financials_sets_transaction_fields(self):
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("240.00"),
            total=Decimal("240.00"),
        )

        apply_order_financials(
            order,
            payment_provider=PaymentProvider.ASAAS,
            financial_transaction_id="pay_abc",
            mark_available=True,
        )
        order.refresh_from_db()

        self.assertEqual(order.payment_provider, PaymentProvider.ASAAS)
        self.assertEqual(order.financial_transaction_id, "pay_abc")
        self.assertEqual(order.administrative_fee, Decimal("1.99"))
        self.assertEqual(order.net_amount, Decimal("238.01"))
        self.assertEqual(order.deposit_status, DepositStatus.AVAILABLE)
        self.assertIsNotNone(order.expected_deposit_date)


class RegistrationCheckoutServiceTestCase(TestCase):
    def setUp(self):
        seed_class_catalog()

    def test_child_kids_and_juvenile_selection_doubles_plan(self):
        kids = ClassCategory.objects.get(code="kids")
        juvenile = ClassCategory.objects.get(code="juvenile")
        payload = {
            "registration_profile": "guardian",
            "student_birthdate": date(2014, 5, 1),
            "student_biological_sex": BiologicalSex.MALE,
            "student_class_groups": [
                kids.class_groups.first(),
                juvenile.class_groups.first(),
            ],
            "extra_dependents": [],
        }

        self.assertEqual(get_registration_plan_multiplier(payload), 2)

    def test_single_child_category_keeps_plan_simple(self):
        kids = ClassCategory.objects.get(code="kids")
        payload = {
            "registration_profile": "guardian",
            "student_birthdate": date(2014, 5, 1),
            "student_biological_sex": BiologicalSex.MALE,
            "student_class_groups": [kids.class_groups.first()],
            "extra_dependents": [],
        }

        self.assertEqual(get_registration_plan_multiplier(payload), 1)
