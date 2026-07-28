from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models.product import Product, ProductCategory
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class ProductCategoryCrudTestCase(TestCase):

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-product-category",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.category = ProductCategory.objects.create(
            code="uniforms-crud-fundacao",
            display_name="Uniformes CRUD",
        )
        self._login_technical_admin()

    def test_english_list_route_renders(self):
        response = self.client.get(reverse("system:product-category-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/materials/categories/")

    def test_create_category_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:product-category-create") + "?modal=1",
            data={
                "code": "rashguards-crud-fundacao",
                "display_name": "Rash Guards CRUD",
                "display_order": "0",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(
            ProductCategory.objects.filter(code="rashguards-crud-fundacao").exists()
        )

    def test_delete_category_with_products_is_blocked(self):
        Product.objects.create(
            sku="SKU-CATEGORY-CRUD-1",
            display_name="Produto Vinculado",
            category=self.category,
            unit_price="10.00",
        )
        response = self.client.post(
            reverse("system:product-category-delete", kwargs={"pk": self.category.pk})
        )
        self.assertRedirects(response, reverse("system:product-category-list"))
        self.assertTrue(ProductCategory.objects.filter(pk=self.category.pk).exists())

    def test_delete_category_without_products_succeeds(self):
        response = self.client.post(
            reverse("system:product-category-delete", kwargs={"pk": self.category.pk})
        )
        self.assertRedirects(response, reverse("system:product-category-list"))
        self.assertFalse(ProductCategory.objects.filter(pk=self.category.pk).exists())

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
