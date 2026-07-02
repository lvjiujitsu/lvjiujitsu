from datetime import date

from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Person,
    PersonType,
    PortalAccount,
    Product,
    ProductBackorder,
    ProductCategory,
    ProductVariant,
)
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.models.registration_order import OrderKind, PaymentStatus, RegistrationOrder
from system.services import PORTAL_ACCOUNT_SESSION_KEY


class ProductStoreTestCase(TestCase):
    """PRD-101: loja publica, pre-pedidos e historico do aluno."""

    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.category = ProductCategory.objects.create(
            code="uniforms-store-fundacao",
            display_name="Uniformes",
        )
        self.product = Product.objects.create(
            sku="STORE-SKU-1",
            display_name="Kimono Loja Fundacao",
            category=self.category,
            unit_price="350.00",
        )
        self.in_stock_variant = ProductVariant.objects.create(
            product=self.product,
            size="M",
            color="Preto",
            stock_quantity=5,
        )
        self.out_of_stock_variant = ProductVariant.objects.create(
            product=self.product,
            size="G",
            color="Preto",
            stock_quantity=0,
        )
        self.student = Person.objects.create(
            full_name="Aluno Loja Fundacao",
            cpf="390.533.447-05",
            person_type=self.student_type,
            birth_date=date(1995, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self._login_as(self.student)

    def test_product_store_renders(self):
        response = self.client.get(reverse("system:product-store"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kimono Loja Fundacao")

    def test_buy_in_stock_variant_creates_order_and_redirects_to_checkout(self):
        response = self.client.post(
            reverse("system:product-order-create"),
            data={
                "cart_payload": (
                    f'[{{"variant_id": {self.in_stock_variant.pk}, "qty": 1}}]'
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/pagamentos/", response["Location"])

    def test_request_backorder_for_out_of_stock_variant(self):
        response = self.client.post(
            reverse("system:product-backorder-create"),
            data={"variant_id": self.out_of_stock_variant.pk},
        )
        self.assertRedirects(response, reverse("system:student-backorders"))
        self.assertTrue(
            ProductBackorder.objects.filter(
                person=self.student, variant=self.out_of_stock_variant
            ).exists()
        )

    def test_backorder_list_renders_and_cancel_updates_status(self):
        backorder = ProductBackorder.objects.create(
            person=self.student, variant=self.out_of_stock_variant
        )
        list_response = self.client.get(reverse("system:student-backorders"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Kimono Loja Fundacao")

        cancel_response = self.client.post(
            reverse("system:student-backorder-cancel", kwargs={"pk": backorder.pk})
        )
        self.assertRedirects(cancel_response, reverse("system:student-backorders"))
        backorder.refresh_from_db()
        self.assertEqual(backorder.status, "canceled")

    def test_order_history_renders_empty_state(self):
        response = self.client.get(reverse("system:student-order-history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum pedido pago ainda.")

    def _login_as(self, person):
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()


class GuardianBuysForDependentTestCase(TestCase):
    """PRD-106: responsavel compra/ve materiais em nome do dependente."""

    def setUp(self):
        self.guardian_type = PersonType.objects.create(
            code=PersonTypeCode.GUARDIAN,
            display_name="Responsável",
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.category = ProductCategory.objects.create(
            code="uniforms-guardian-fundacao",
            display_name="Uniformes",
        )
        self.product = Product.objects.create(
            sku="STORE-SKU-GUARDIAN-1",
            display_name="Kimono Dependente Fundacao",
            category=self.category,
            unit_price="350.00",
        )
        self.out_of_stock_variant = ProductVariant.objects.create(
            product=self.product,
            size="M",
            color="Preto",
            stock_quantity=0,
        )
        self.guardian = Person.objects.create(
            full_name="Responsável Loja Fundacao",
            cpf="390.533.447-05",
            person_type=self.guardian_type,
            birth_date=date(1980, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Loja Fundacao",
            cpf="529.982.247-25",
            person_type=self.student_type,
            birth_date=date(2012, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        PersonRelationship.objects.create(
            source_person=self.guardian,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        self._login_as(self.guardian)

    def test_store_shows_dependent_in_purchase_person_selector(self):
        response = self.client.get(reverse("system:product-store"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dependente Loja Fundacao")

    def test_backorder_created_for_dependent_appears_in_guardian_list(self):
        self.client.post(
            reverse("system:product-backorder-create"),
            data={
                "variant_id": self.out_of_stock_variant.pk,
                "purchase_person_id": self.dependent.pk,
            },
        )
        self.assertTrue(
            ProductBackorder.objects.filter(
                person=self.dependent, variant=self.out_of_stock_variant
            ).exists()
        )
        response = self.client.get(reverse("system:student-backorders"))
        self.assertContains(response, "Kimono Dependente Fundacao")

    def test_paid_order_for_dependent_appears_in_guardian_history(self):
        order = RegistrationOrder.objects.create(
            person=self.dependent,
            plan=None,
            plan_price=0,
            total=350,
            kind=OrderKind.ONE_TIME,
            payment_status=PaymentStatus.PAID,
        )
        response = self.client.get(reverse("system:student-order-history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 pedido")
        self.assertContains(response, f"Pedido #{order.pk}")

    def _login_as(self, person):
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()
