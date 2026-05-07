from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from system.models import (
    Person,
    PersonType,
    Product,
    ProductBackorder,
    ProductBackorderStatus,
    ProductCategory,
    ProductVariant,
)
from system.services.product_backorders import (
    ProductBackorderError,
    cancel_backorder,
    confirm_backorder,
    create_backorder,
    expire_pending_reservations,
    restock_variant,
)


class BackorderTestData:
    @classmethod
    def build(cls):
        person_type = PersonType.objects.create(code="student", display_name="Aluno")
        person_a = Person.objects.create(
            full_name="Aluno A", cpf="100.000.000-01", person_type=person_type,
        )
        person_b = Person.objects.create(
            full_name="Aluno B", cpf="100.000.000-02", person_type=person_type,
        )
        category = ProductCategory.objects.create(
            code="kimonos", display_name="Kimonos",
        )
        product = Product.objects.create(
            sku="gi-test", display_name="Kimono Teste",
            category=category, unit_price=Decimal("480.00"),
        )
        variant = ProductVariant.objects.create(
            product=product, color="Branco", size="A2", stock_quantity=0,
        )
        return person_type, person_a, person_b, product, variant


class CreateBackorderTestCase(TestCase):
    def setUp(self):
        _, self.person_a, self.person_b, _, self.variant = BackorderTestData.build()

    def test_create_backorder_creates_pending(self):
        backorder = create_backorder(self.person_a, self.variant)
        self.assertEqual(backorder.status, ProductBackorderStatus.PENDING)
        self.assertEqual(backorder.person, self.person_a)
        self.assertEqual(backorder.variant, self.variant)

    def test_create_duplicate_returns_existing(self):
        first = create_backorder(self.person_a, self.variant)
        second = create_backorder(self.person_a, self.variant)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(ProductBackorder.objects.count(), 1)

    def test_create_inactive_variant_raises(self):
        self.variant.is_active = False
        self.variant.save()
        with self.assertRaises(ProductBackorderError):
            create_backorder(self.person_a, self.variant)


class RestockVariantTestCase(TestCase):
    def setUp(self):
        _, self.person_a, self.person_b, _, self.variant = BackorderTestData.build()

    def test_restock_promotes_pending_in_order(self):
        first = create_backorder(self.person_a, self.variant)
        second = create_backorder(self.person_b, self.variant)

        promoted = restock_variant(self.variant, 1)

        self.assertEqual(len(promoted), 1)
        self.assertEqual(promoted[0].pk, first.pk)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, ProductBackorderStatus.READY)
        self.assertEqual(second.status, ProductBackorderStatus.PENDING)

    def test_restock_with_more_units_promotes_all(self):
        create_backorder(self.person_a, self.variant)
        create_backorder(self.person_b, self.variant)

        promoted = restock_variant(self.variant, 5)

        self.assertEqual(len(promoted), 2)
        ready_count = ProductBackorder.objects.filter(
            status=ProductBackorderStatus.READY
        ).count()
        self.assertEqual(ready_count, 2)

    def test_restock_signal_promotes_on_stock_increase(self):
        create_backorder(self.person_a, self.variant)
        self.variant.stock_quantity = 1
        self.variant.save()

        backorder = ProductBackorder.objects.get(person=self.person_a)
        self.assertEqual(backorder.status, ProductBackorderStatus.READY)
        self.assertIsNotNone(backorder.notified_at)
        self.assertIsNotNone(backorder.expires_at)


class ConfirmBackorderTestCase(TestCase):
    def setUp(self):
        _, self.person_a, _, self.product, self.variant = BackorderTestData.build()
        self.backorder = create_backorder(self.person_a, self.variant)
        restock_variant(self.variant, 1)
        self.backorder.refresh_from_db()

    def test_confirm_creates_order_and_marks_confirmed(self):
        order = confirm_backorder(self.backorder)
        self.backorder.refresh_from_db()

        self.assertEqual(self.backorder.status, ProductBackorderStatus.CONFIRMED)
        self.assertEqual(self.backorder.confirmed_order, order)
        self.assertEqual(order.total, self.product.unit_price)
        self.assertEqual(order.items.count(), 1)

    def test_confirm_pending_raises(self):
        self.backorder.status = ProductBackorderStatus.PENDING
        self.backorder.save()
        with self.assertRaises(ProductBackorderError):
            confirm_backorder(self.backorder)


class CancelBackorderTestCase(TestCase):
    def setUp(self):
        _, self.person_a, self.person_b, _, self.variant = BackorderTestData.build()

    def test_cancel_pending_marks_canceled(self):
        backorder = create_backorder(self.person_a, self.variant)
        cancel_backorder(backorder)
        backorder.refresh_from_db()
        self.assertEqual(backorder.status, ProductBackorderStatus.CANCELED)

    def test_cancel_ready_promotes_next_in_queue(self):
        first = create_backorder(self.person_a, self.variant)
        second = create_backorder(self.person_b, self.variant)
        restock_variant(self.variant, 1)
        first.refresh_from_db()
        self.assertEqual(first.status, ProductBackorderStatus.READY)

        cancel_backorder(first)
        second.refresh_from_db()
        self.assertEqual(second.status, ProductBackorderStatus.READY)


class ExpireBackordersTestCase(TestCase):
    def setUp(self):
        _, self.person_a, self.person_b, _, self.variant = BackorderTestData.build()

    def test_expire_promotes_next_in_queue(self):
        first = create_backorder(self.person_a, self.variant)
        second = create_backorder(self.person_b, self.variant)
        restock_variant(self.variant, 1)
        first.refresh_from_db()

        first.expires_at = timezone.now() - timedelta(hours=1)
        first.save()

        result = expire_pending_reservations()
        self.assertEqual(len(result["expired"]), 1)
        self.assertEqual(len(result["promoted"]), 1)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, ProductBackorderStatus.EXPIRED)
        self.assertEqual(second.status, ProductBackorderStatus.READY)


class ExpireBackordersCommandTestCase(TestCase):
    def test_command_runs_without_error_on_empty(self):
        output = StringIO()

        call_command("expire_backorders", stdout=output)

        self.assertIn("Nenhuma reserva expirada encontrada.", output.getvalue())


class VariantDeactivationCancelsBackordersTestCase(TestCase):
    def setUp(self):
        _, self.person_a, _, _, self.variant = BackorderTestData.build()

    def test_deactivating_variant_cancels_active_backorders(self):
        backorder = create_backorder(self.person_a, self.variant)

        self.variant.is_active = False
        self.variant.save()

        backorder.refresh_from_db()
        self.assertEqual(backorder.status, ProductBackorderStatus.CANCELED)
