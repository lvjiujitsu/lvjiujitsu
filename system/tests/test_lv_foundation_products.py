from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models.product import Product, ProductCategory
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationProductsRoutesTestCase(TestCase):
    """PRD-077: rotas canonicas em ingles + CRUD curto em modal para Materiais."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-products",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.category = ProductCategory.objects.create(
            code="uniforms-fundacao",
            display_name="Uniformes",
        )
        self.product = Product.objects.create(
            sku="SKU-FUNDACAO-1",
            display_name="Kimono Fundacao",
            category=self.category,
            unit_price="350.00",
        )
        self._login_technical_admin()

    def test_english_product_list_route_renders(self):
        response = self.client.get(reverse("system:product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/materials/")

    def test_old_portuguese_list_route_redirects_to_english(self):
        response = self.client.get("/materiais/")
        self.assertRedirects(response, reverse("system:product-list"))

    def test_create_product_modal_renders_modal_template_with_variant_formset(self):
        response = self.client.get(reverse("system:product-create") + "?modal=1")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_form.html")
        self.assertIn("variant_formset", response.context)

    def test_create_product_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:product-create") + "?modal=1",
            data={
                "sku": "SKU-FUNDACAO-2",
                "display_name": "Rash Guard Fundacao",
                "category": self.category.pk,
                "unit_price": "120.00",
                "description": "",
                "is_active": "on",
                "variants-TOTAL_FORMS": "1",
                "variants-INITIAL_FORMS": "0",
                "variants-MIN_NUM_FORMS": "0",
                "variants-MAX_NUM_FORMS": "1000",
                "variants-0-size": "M",
                "variants-0-color": "Preto",
                "variants-0-stock_quantity": "10",
                "variants-0-is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(Product.objects.filter(sku="SKU-FUNDACAO-2").exists())

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
