from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    Person,
    PersonType,
    RegistrationOrder,
    RegistrationOrderItem,
    SubscriptionPlan,
)
from system.models.product import Product, ProductCategory, ProductVariant
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.models.registration_order import DepositStatus, PaymentProvider
from system.services.financial_transactions import (
    apply_order_financials,
    calculate_financial_amounts,
)
from system.services.membership import add_billing_cycle, mark_order_manually_paid
from system.services.registration_checkout import (
    create_product_only_order,
    get_registration_plan_multiplier,
)
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


class MembershipBillingCycleTestCase(TestCase):
    def test_add_billing_cycle_uses_calendar_month_boundaries(self):
        start = timezone.make_aware(datetime(2026, 1, 31, 12, 0))

        result = add_billing_cycle(start, BillingCycle.MONTHLY)

        self.assertEqual(result.date(), date(2026, 2, 28))


class RegistrationCheckoutServiceTestCase(TestCase):
    def setUp(self):
        seed_class_catalog()

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
