import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import PersonType, Person, PortalAccount, ProductBackorder, RegistrationOrder
from system.models.product import Product, ProductCategory, ProductVariant
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY
from system.services.seeding import seed_products

User = get_user_model()


class ProductViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin",
        )
        self.admin_type = PersonType.objects.create(
            code="administrative-assistant",
            display_name="Auxiliar administrativo",
        )
        self.student_type = PersonType.objects.create(
            code="student", display_name="Aluno",
        )
        self.instructor_type = PersonType.objects.create(
            code="instructor", display_name="Professor",
        )
        self.category = ProductCategory.objects.create(
            code="kimonos", display_name="Kimonos",
        )
        self.product = Product.objects.create(
            sku="gi-view-test",
            display_name="Kimono View Test",
            category=self.category,
            unit_price=Decimal("480.00"),
        )
        ProductVariant.objects.create(
            product=self.product, color="Branco", stock_quantity=2,
        )
        self.portal_account = self._create_portal_account(
            full_name="Admin Teste",
            cpf="111.111.111-11",
            person_type=self.admin_type,
        )

    def _create_portal_account(self, *, full_name, cpf, person_type):
        person = Person.objects.create(
            full_name=full_name, cpf=cpf, person_type=person_type,
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        return account

    def _login_as_admin(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.portal_account.pk
        session[TECHNICAL_ADMIN_SESSION_KEY] = True
        session.save()

    def _login_as_portal(self, account):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_product_list_requires_auth(self):
        response = self.client.get(reverse("system:product-list"))
        self.assertNotEqual(response.status_code, 200)

    def test_product_list_loads(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kimono View Test")

    def test_product_list_uses_annotations(self):
        self._login_as_admin()
        with self.assertNumQueries(6):
            self.client.get(reverse("system:product-list"))

    def test_product_detail_loads(self):
        self._login_as_admin()
        response = self.client.get(
            reverse("system:product-detail", args=[self.product.pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "gi-view-test")
        self.assertContains(response, "Branco")
        self.assertContains(response, "2 un.")

    def test_product_create_page_loads(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:product-create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cadastrar produto")

    def test_product_delete_confirm_loads(self):
        self._login_as_admin()
        response = self.client.get(
            reverse("system:product-delete", args=[self.product.pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Excluir produto")

    def test_product_delete_removes(self):
        self._login_as_admin()
        self.client.post(
            reverse("system:product-delete", args=[self.product.pk]),
        )
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_admin_dashboard_shows_materiais(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:admin-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Materiais")

    def test_administrative_dashboard_shows_materiais(self):
        self._login_as_admin()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.portal_account.pk
        session.pop(TECHNICAL_ADMIN_SESSION_KEY, None)
        session.save()
        response = self.client.get(reverse("system:administrative-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Materiais")

    def test_student_dashboard_shows_materiais_link(self):
        student_account = self._create_portal_account(
            full_name="Aluno Teste",
            cpf="222.222.222-22",
            person_type=self.student_type,
        )
        self._login_as_portal(student_account)
        response = self.client.get(reverse("system:student-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Materiais")

    def test_product_store_exposes_variant_catalog_json(self):
        student_account = self._create_portal_account(
            full_name="Aluno Loja",
            cpf="333.222.111-00",
            person_type=self.student_type,
        )
        self._login_as_portal(student_account)

        response = self.client.get(reverse("system:product-store"))

        self.assertEqual(response.status_code, 200)
        catalog = json.loads(response.context["product_catalog_json"])
        product = next(item for item in catalog if item["sku"] == "gi-view-test")
        self.assertEqual(product["category"], "Kimonos")
        self.assertGreater(product["variant_count"], 0)
        self.assertEqual(product["variants"][0]["color"], "Branco")
        self.assertIn("snapshot_name", product["variants"][0])

    def test_instructor_product_store_exposes_student_recipient_choices(self):
        instructor_account = self._create_portal_account(
            full_name="Professor Materiais",
            cpf="333.222.111-01",
            person_type=self.instructor_type,
        )
        student_person = Person.objects.create(
            full_name="Aluno Compras",
            cpf="333.222.111-02",
            person_type=self.student_type,
        )
        self._login_as_portal(instructor_account)

        response = self.client.get(reverse("system:product-store"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solicitar para")
        self.assertContains(response, instructor_account.person.full_name)
        self.assertContains(response, student_person.full_name)

    def test_administrative_product_store_opens_as_portal_person(self):
        self._login_as_portal(self.portal_account)

        response = self.client.get(reverse("system:product-store"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Materiais")

    def test_instructor_can_checkout_material_for_selected_student(self):
        instructor_account = self._create_portal_account(
            full_name="Professor Pedido",
            cpf="333.222.111-03",
            person_type=self.instructor_type,
        )
        student_person = Person.objects.create(
            full_name="Aluno Pedido",
            cpf="333.222.111-04",
            person_type=self.student_type,
        )
        variant = self.product.variants.first()
        self._login_as_portal(instructor_account)

        response = self.client.post(
            reverse("system:product-store-checkout"),
            {
                "cart_payload": json.dumps([
                    {"variant_id": variant.pk, "qty": 1},
                ]),
                "purchase_person_id": student_person.pk,
            },
        )

        order = RegistrationOrder.objects.get()
        self.assertEqual(order.person, student_person)
        self.assertRedirects(
            response,
            reverse("system:payment-checkout", kwargs={"order_id": order.pk}),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            self.client.session.get("pending_checkout_order_id"),
            order.pk,
        )

    def test_instructor_can_create_backorder_for_selected_student(self):
        instructor_account = self._create_portal_account(
            full_name="Professor Pre Pedido",
            cpf="333.222.111-05",
            person_type=self.instructor_type,
        )
        student_person = Person.objects.create(
            full_name="Aluno Pre Pedido",
            cpf="333.222.111-06",
            person_type=self.student_type,
        )
        variant = ProductVariant.objects.create(
            product=self.product,
            color="Azul",
            size="A2",
            stock_quantity=0,
        )
        self._login_as_portal(instructor_account)

        response = self.client.post(
            reverse("system:product-backorder-create"),
            {
                "variant_id": variant.pk,
                "purchase_person_id": student_person.pk,
            },
        )

        backorder = ProductBackorder.objects.get()
        self.assertEqual(backorder.person, student_person)
        self.assertRedirects(response, reverse("system:student-backorders"))

    def test_update_redirects_to_detail(self):
        self._login_as_admin()
        response = self.client.post(
            reverse("system:product-update", args=[self.product.pk]),
            {
                "sku": "gi-view-test",
                "display_name": "Kimono Editado",
                "category": self.category.pk,
                "unit_price": "480.00",
                "is_active": "on",
                "variants-TOTAL_FORMS": "1",
                "variants-INITIAL_FORMS": "1",
                "variants-MIN_NUM_FORMS": "0",
                "variants-MAX_NUM_FORMS": "1000",
                "variants-0-id": self.product.variants.first().pk,
                "variants-0-product": self.product.pk,
                "variants-0-color": "Branco",
                "variants-0-size": "",
                "variants-0-stock_quantity": "2",
                "variants-0-is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/products/{self.product.pk}/", response.url)
