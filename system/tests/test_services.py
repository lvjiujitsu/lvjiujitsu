from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from system.models import (
    BiologicalSex,
    CategoryAudience,
    CheckinStatus,
    ClassCategory,
    ClassCheckin,
    Person,
    PersonType,
    RegistrationOrder,
    RegistrationOrderItem,
    ClassEnrollment,
    ClassGroup,
    ClassSchedule,
    ClassSession,
    PayoutKind,
    PayoutStatus,
    SubscriptionPlan,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
    WeekdayCode,
)
from system.models.product import Product, ProductCategory, ProductVariant
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.models.registration_order import DepositStatus, PaymentProvider, PaymentStatus
from system.models.asaas import PixKeyType
from system.services.financial_dashboard import build_financial_dashboard
from system.services.financial_transactions import (
    apply_order_financials,
    calculate_financial_amounts,
)
from system.services.membership import add_billing_cycle, mark_order_manually_paid
from system.services.payroll_rules import (
    PAYROLL_METHOD_FIXED_MONTHLY,
    PAYROLL_METHOD_PER_CLASS_ATTENDANCE,
    PAYROLL_METHOD_STUDENT_PERCENTAGE,
    calculate_monthly_payroll,
    encode_payroll_rules,
)
from system.services.registration_checkout import (
    create_product_only_order,
    get_registration_plan_multiplier,
)
from system.services.seeding import seed_ibjjf_age_categories
from system.tests.seed_helpers import seed_full_class_catalog


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

    @override_settings(ASAAS_PIX_FIXED_FEE="2.50")
    def test_calculates_asaas_pix_fee_from_settings(self):
        result = calculate_financial_amounts(Decimal("240.00"), PaymentProvider.ASAAS)

        self.assertEqual(result["administrative_fee"], Decimal("2.50"))
        self.assertEqual(result["net_amount"], Decimal("237.50"))

    @override_settings(
        STRIPE_CREDIT_PERCENT_FEE="0.05",
        STRIPE_CREDIT_FIXED_FEE="1.00",
    )
    def test_calculates_stripe_credit_fee_from_settings(self):
        result = calculate_financial_amounts(Decimal("250.00"), PaymentProvider.STRIPE)

        self.assertEqual(result["administrative_fee"], Decimal("13.50"))
        self.assertEqual(result["net_amount"], Decimal("236.50"))

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


class FinancialDashboardServiceTestCase(TestCase):
    def setUp(self):
        seed_ibjjf_age_categories()
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.instructor_type = PersonType.objects.create(
            code="instructor",
            display_name="Professor",
        )
        self.person = Person.objects.create(
            full_name="Aluno Painel",
            cpf="111.222.333-45",
            person_type=self.student_type,
        )
        self.teacher = Person.objects.create(
            full_name="Professor Painel",
            cpf="111.222.333-46",
            person_type=self.instructor_type,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="dashboard-pix",
            display_name="Dashboard PIX",
            price=Decimal("200.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
        )
        self.order = RegistrationOrder.objects.create(
            person=self.person,
            plan=self.plan,
            plan_price=Decimal("200.00"),
            total=Decimal("200.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.ASAAS,
            administrative_fee=Decimal("1.99"),
            net_amount=Decimal("198.01"),
            deposit_status=DepositStatus.AVAILABLE,
            expected_deposit_date=date(2026, 4, 20),
            paid_at=timezone.now(),
        )
        bank = TeacherBankAccount.objects.create(
            person=self.teacher,
            pix_key="pix",
            pix_key_type=PixKeyType.EVP,
        )
        TeacherPayout.objects.create(
            person=self.teacher,
            bank_account=bank,
            kind=PayoutKind.PAYROLL,
            reference_month=date(2026, 4, 1),
            amount=Decimal("100.00"),
            status=PayoutStatus.PAID,
            scheduled_for=date(2026, 4, 28),
            approval_notes="Fechamento de abril.",
        )

    @override_settings(ASAAS_API_KEY="asaas", ASAAS_API_URL="https://sandbox.asaas.com/api/v3", STRIPE_SECRET_KEY="sk_test")
    @patch("system.services.financial_dashboard.stripe.Balance.retrieve")
    @patch("system.services.financial_dashboard.asaas_client.get_payment_statistics")
    @patch("system.services.financial_dashboard.asaas_client.get_balance")
    def test_build_financial_dashboard_combines_gateways_and_history(
        self,
        mock_asaas_balance,
        mock_asaas_stats,
        mock_stripe_balance,
    ):
        mock_asaas_balance.return_value = {"balance": 5210.96}
        mock_asaas_stats.return_value = {
            "quantity": 2,
            "value": 9270.40,
            "netValue": 9121.54,
        }
        mock_stripe_balance.return_value = {
            "available": [{"amount": 123456, "currency": "brl"}],
            "pending": [{"amount": 6543, "currency": "brl"}],
        }

        dashboard = build_financial_dashboard()

        self.assertEqual(dashboard["asaas"]["available"], Decimal("5210.96"))
        self.assertEqual(dashboard["asaas"]["receivable"], Decimal("9121.54"))
        self.assertEqual(dashboard["stripe"]["available"], Decimal("1234.56"))
        self.assertEqual(dashboard["stripe"]["receivable"], Decimal("65.43"))
        self.assertEqual(dashboard["totals"]["receivable"], Decimal("9186.97"))
        self.assertEqual(dashboard["totals"]["local_receivable"], Decimal("198.01"))
        self.assertEqual(dashboard["totals"]["outflows"], Decimal("100.00"))
        self.assertTrue(any(entry["direction"] == "outflow" for entry in dashboard["history"]))
        self.assertTrue(any(entry["person"] == self.person for entry in dashboard["history"]))


class PayrollRulesServiceTestCase(TestCase):
    def setUp(self):
        seed_ibjjf_age_categories()
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.instructor_type = PersonType.objects.create(
            code="instructor",
            display_name="Professor",
        )
        self.teacher = Person.objects.create(
            full_name="Professor Regra",
            cpf="222.333.444-55",
            person_type=self.instructor_type,
        )
        self.student = Person.objects.create(
            full_name="Aluno Regra",
            cpf="222.333.444-56",
            birth_date=date(2010, 1, 1),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
        )
        self.category = ClassCategory.objects.create(
            code="juvenile-rules",
            display_name="Juvenil",
            audience=CategoryAudience.JUVENILE,
        )
        self.group = ClassGroup.objects.create(
            code="juvenile-rules",
            display_name="Jiu Jitsu",
            class_category=self.category,
            main_teacher=self.teacher,
        )
        ClassEnrollment.objects.create(
            class_group=self.group,
            person=self.student,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="rules-plan",
            display_name="Plano Regras",
            price=Decimal("200.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
        )
        self.order = RegistrationOrder.objects.create(
            person=self.student,
            plan=self.plan,
            plan_price=Decimal("200.00"),
            total=Decimal("200.00"),
            payment_status=PaymentStatus.PAID,
            payment_provider=PaymentProvider.ASAAS,
            net_amount=Decimal("198.00"),
            paid_at=timezone.make_aware(datetime(2026, 4, 10, 10, 0)),
        )

    def test_calculates_fixed_monthly_plus_student_percentage_rules(self):
        TeacherPayrollConfig.objects.create(
            person=self.teacher,
            monthly_salary=Decimal("400.00"),
            payment_day=28,
            notes=encode_payroll_rules(
                [
                    {
                        "method": PAYROLL_METHOD_FIXED_MONTHLY,
                        "amount": "400.00",
                        "scope": "class_group",
                        "class_group_code": self.group.code,
                    },
                    {
                        "method": PAYROLL_METHOD_STUDENT_PERCENTAGE,
                        "percentage": "50.00",
                        "scope": "class_group",
                        "class_group_code": self.group.code,
                    },
                ]
            ),
        )

        result = calculate_monthly_payroll(
            self.teacher,
            reference_month=date(2026, 4, 1),
        )

        self.assertEqual(result["total"], Decimal("499.00"))
        self.assertEqual(result["fixed_total"], Decimal("400.00"))
        self.assertEqual(result["student_total"], Decimal("99.00"))
        self.assertEqual(result["student_count"], 1)
        self.assertEqual(result["entries"][0]["person"], self.student)

    def test_calculates_per_class_attendance_rule(self):
        schedule = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=WeekdayCode.MONDAY,
            start_time="18:00",
            training_style="gi",
        )
        session = ClassSession.objects.create(
            schedule=schedule,
            date=date(2026, 4, 6),
        )
        ClassCheckin.objects.create(
            session=session,
            person=self.student,
            status=CheckinStatus.APPROVED,
        )
        TeacherPayrollConfig.objects.create(
            person=self.teacher,
            monthly_salary=Decimal("0.00"),
            payment_day=28,
            notes=encode_payroll_rules(
                [
                    {
                        "method": PAYROLL_METHOD_PER_CLASS_ATTENDANCE,
                        "amount": "25.00",
                        "scope": "class_group",
                        "class_group_code": self.group.code,
                    },
                ]
            ),
        )

        result = calculate_monthly_payroll(
            self.teacher,
            reference_month=date(2026, 4, 1),
        )

        self.assertEqual(result["total"], Decimal("25.00"))
        self.assertEqual(result["class_total"], Decimal("25.00"))
        self.assertEqual(result["class_attendance_count"], 1)


class MembershipBillingCycleTestCase(TestCase):
    def test_add_billing_cycle_uses_calendar_month_boundaries(self):
        start = timezone.make_aware(datetime(2026, 1, 31, 12, 0))

        result = add_billing_cycle(start, BillingCycle.MONTHLY)

        self.assertEqual(result.date(), date(2026, 2, 28))


class RegistrationCheckoutServiceTestCase(TestCase):
    def setUp(self):
        seed_full_class_catalog()

    def test_plan_multiplier_is_always_one(self):
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

        self.assertEqual(get_registration_plan_multiplier(payload), 1)

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


class ProductCheckoutServiceTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.person = Person.objects.create(
            full_name="Aluno Loja",
            cpf="999.888.777-66",
            person_type=self.person_type,
        )
        self.category = ProductCategory.objects.create(
            code="kimonos",
            display_name="Kimonos",
        )
        self.product = Product.objects.create(
            sku="gi-lv-teste",
            display_name="Kimono LV Teste",
            category=self.category,
            unit_price=Decimal("480.00"),
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color="Azul",
            size="A2",
            stock_quantity=2,
        )

    def test_create_product_only_order_keeps_variant_snapshot_in_item_name(self):
        order = create_product_only_order(
            self.person,
            [{"variant_id": self.variant.pk, "quantity": 1}],
        )

        self.assertIsNotNone(order)
        item = order.items.get()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.product_name, "Kimono LV Teste (Cor: Azul, Tamanho: A2)")
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.subtotal, Decimal("480.00"))

    def test_mark_order_manually_paid_decrements_variant_stock_once(self):
        order = create_product_only_order(
            self.person,
            [{"variant_id": self.variant.pk, "quantity": 2}],
        )

        mark_order_manually_paid(order, admin_user=None, notes="Pagamento confirmado")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 0)

        mark_order_manually_paid(order, admin_user=None, notes="Retry")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 0)

    def test_mark_order_manually_paid_preserves_item_snapshot_after_stock_update(self):
        order = create_product_only_order(
            self.person,
            [{"variant_id": self.variant.pk, "quantity": 1}],
        )

        mark_order_manually_paid(order, admin_user=None, notes="Pago")
        item = RegistrationOrderItem.objects.get(order=order)

        self.assertEqual(item.product_name, "Kimono LV Teste (Cor: Azul, Tamanho: A2)")
