from decimal import Decimal

from django.test import TestCase

from system.models.product import Product, ProductCategory, ProductVariant
class ProductCategoryModelTestCase(TestCase):
    def test_create_category(self):
        cat = ProductCategory.objects.create(
            code="test-cat",
            display_name="Categoria Teste",
            display_order=1,
        )
        self.assertEqual(str(cat), "Categoria Teste")
        self.assertTrue(cat.is_active)

    def test_code_is_unique(self):
        ProductCategory.objects.create(code="unique", display_name="A")
        with self.assertRaises(Exception):
            ProductCategory.objects.create(code="unique", display_name="B")


class ProductModelTestCase(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(
            code="kimonos",
            display_name="Kimonos",
        )

    def test_create_product(self):
        product = Product.objects.create(
            sku="gi-test",
            display_name="Kimono Teste",
            category=self.category,
            unit_price=Decimal("480.00"),
        )
        self.assertEqual(str(product), "Kimono Teste")
        self.assertTrue(product.is_active)
        self.assertEqual(product.total_stock, 0)
        self.assertEqual(product.variant_count, 0)
        self.assertFalse(product.is_in_stock)

    def test_sku_is_unique(self):
        Product.objects.create(
            sku="sku-dup",
            display_name="A",
            category=self.category,
            unit_price=Decimal("100.00"),
        )
        with self.assertRaises(Exception):
            Product.objects.create(
                sku="sku-dup",
                display_name="B",
                category=self.category,
                unit_price=Decimal("200.00"),
            )

    def test_total_stock_with_variants(self):
        product = Product.objects.create(
            sku="gi-stock",
            display_name="Kimono Stock",
            category=self.category,
            unit_price=Decimal("480.00"),
        )
        ProductVariant.objects.create(
            product=product, color="Branco", stock_quantity=3,
        )
        ProductVariant.objects.create(
            product=product, color="Preto", stock_quantity=5,
        )
        self.assertEqual(product.total_stock, 8)
        self.assertEqual(product.variant_count, 2)
        self.assertTrue(product.is_in_stock)


class ProductVariantModelTestCase(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(
            code="belts", display_name="Faixas",
        )
        self.product = Product.objects.create(
            sku="belt-test",
            display_name="Faixa Teste",
            category=self.category,
            unit_price=Decimal("75.00"),
        )

    def test_create_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            color="Azul",
            size="",
            stock_quantity=2,
        )
        self.assertIn("Azul", str(variant))
        self.assertTrue(variant.is_in_stock)

    def test_out_of_stock_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            color="Roxa",
            stock_quantity=0,
        )
        self.assertFalse(variant.is_in_stock)

    def test_unique_variant_constraint(self):
        ProductVariant.objects.create(
            product=self.product, color="Branca", size="",
        )
        with self.assertRaises(Exception):
            ProductVariant.objects.create(
                product=self.product, color="Branca", size="",
            )


