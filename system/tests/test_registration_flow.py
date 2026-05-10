"""
Testes para o fluxo revisado de cadastro (PRD-021).

Comportamento esperado:
- Ao submeter o wizard, Person é criado com is_active=False
- CPF de Person inativa pode ser reutilizado (sem "CPF já cadastrado")
- Após pagamento do plano, redirect vai para /register/ (não login)
- MaterialsCheckoutView cria order separado de materiais
- FinalizeRegistrationView seta person.is_active=True e faz login
- DeferPaymentView redireciona para /register/ (não login)
- PaymentCancelView redireciona para /register/ (não login)
"""
import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from system.models import (
    Person,
    PersonType,
    PortalAccount,
    RegistrationOrder,
    SubscriptionPlan,
    TrialAccessGrant,
)
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.models.registration_order import OrderKind, PaymentStatus
from system.models.product import Product, ProductCategory, ProductVariant
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.seeding import seed_belts


class RegistrationFlowTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_belts()
        cls.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        cls.dependent_type = PersonType.objects.create(code="dependent", display_name="Dependente")
        cls.plan = SubscriptionPlan.objects.create(
            code="mensal-pix-test",
            display_name="Plano Mensal PIX",
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            price=Decimal("240.00"),
            is_active=True,
        )
        category = ProductCategory.objects.create(
            code="faixas",
            display_name="Faixas",
            display_order=1,
            is_active=True,
        )
        cls.product = Product.objects.create(
            sku="FAIXA-001",
            display_name="Faixa LV",
            unit_price=Decimal("75.00"),
            category=category,
            is_active=True,
        )
        cls.variant = ProductVariant.objects.create(
            product=cls.product,
            color="Branca",
            size="A1",
            stock_quantity=10,
            is_active=True,
        )

    def _register_payload(self, cpf="12345678901"):
        return {
            "registration_profile": "holder",
            "holder_name": "Aluno Teste",
            "holder_cpf": cpf,
            "holder_birthdate": "01/04/1995",
            "holder_biological_sex": "male",
            "holder_phone": "(62) 99999-0000",
            "holder_email": "teste@example.com",
            "holder_password": "senha123",
            "holder_password_confirm": "senha123",
            "selected_plan": str(self.plan.pk),
            "checkout_action": "pay_later",
        }

    # -----------------------------------------------------------------------
    # Person.is_active=False ao submeter o form
    # -----------------------------------------------------------------------

    def test_registration_creates_person_with_is_active_false(self):
        self.client.post(reverse("system:register"), self._register_payload())

        person = Person.objects.filter(cpf="123.456.789-01").first()
        self.assertIsNotNone(person)
        self.assertFalse(person.is_active)

    def test_registration_creates_portal_account(self):
        self.client.post(reverse("system:register"), self._register_payload())

        person = Person.objects.get(cpf="123.456.789-01")
        self.assertTrue(hasattr(person, "access_account"))

    def test_registration_stores_pending_person_id_in_session(self):
        self.client.post(reverse("system:register"), self._register_payload())

        person = Person.objects.get(cpf="123.456.789-01")
        self.assertEqual(
            self.client.session.get("pending_registration_person_id"),
            person.pk,
        )

    def test_registration_order_contains_only_plan_no_products(self):
        self.client.post(reverse("system:register"), self._register_payload())

        order = RegistrationOrder.objects.get(person__cpf="123.456.789-01")
        self.assertEqual(order.plan, self.plan)
        self.assertEqual(order.items.count(), 0)

    # -----------------------------------------------------------------------
    # CPF de Person inativa pode ser reutilizado
    # -----------------------------------------------------------------------

    def test_inactive_cpf_can_be_reregistered(self):
        Person.objects.create(
            full_name="Fantasma",
            cpf="123.456.789-01",
            is_active=False,
            person_type=self.student_type,
        )

        response = self.client.post(
            reverse("system:register"),
            self._register_payload("12345678901"),
        )

        self.assertNotIn(
            "CPF já cadastrado no sistema.",
            response.content.decode("utf-8"),
        )
        person = Person.objects.filter(cpf="123.456.789-01").first()
        self.assertIsNotNone(person)

    def test_active_cpf_blocks_registration(self):
        Person.objects.create(
            full_name="Ativo",
            cpf="123.456.789-01",
            is_active=True,
            person_type=self.student_type,
        )
        account = PortalAccount(person=Person.objects.get(cpf="123.456.789-01"))
        account.set_password("x")
        account.save()

        response = self.client.post(
            reverse("system:register"),
            self._register_payload("12345678901"),
        )

        self.assertContains(response, "CPF já cadastrado no sistema.")

    # -----------------------------------------------------------------------
    # Redirecionamentos pós-pagamento
    # -----------------------------------------------------------------------

    def test_pay_later_redirects_to_register_not_login(self):
        response = self.client.post(
            reverse("system:register"),
            self._register_payload(),
            follow=False,
        )

        self.assertNotEqual(response.get("Location"), reverse("system:login"))

    def test_defer_payment_view_redirects_to_register(self):
        self.client.post(reverse("system:register"), self._register_payload())
        order = RegistrationOrder.objects.get(person__cpf="123.456.789-01")

        response = self.client.get(
            reverse("system:payment-defer", kwargs={"order_id": order.pk}),
        )

        self.assertRedirects(response, reverse("system:register"), fetch_redirect_response=False)

    def test_payment_cancel_redirects_to_register(self):
        response = self.client.get(reverse("system:payment-cancel"))

        self.assertRedirects(response, reverse("system:register"), fetch_redirect_response=False)

    def test_payment_success_redirects_to_register_with_plan_flag(self):
        self.client.post(reverse("system:register"), self._register_payload())
        order = RegistrationOrder.objects.get(person__cpf="123.456.789-01")
        session = self.client.session
        session["pending_checkout_order_id"] = order.pk
        session.save()

        response = self.client.get(reverse("system:payment-success"))

        self.assertRedirects(response, reverse("system:register"), fetch_redirect_response=False)
        self.assertTrue(self.client.session.get("post_plan_payment_complete"))

    # -----------------------------------------------------------------------
    # MaterialsCheckoutView
    # -----------------------------------------------------------------------

    def test_materials_checkout_creates_separate_order(self):
        self.client.post(reverse("system:register"), self._register_payload())
        person = Person.objects.get(cpf="123.456.789-01")
        session = self.client.session
        session["pending_registration_person_id"] = person.pk
        session["post_plan_payment_complete"] = True
        session.save()

        payload = json.dumps([{"variant_id": self.variant.pk, "qty": 1}])
        self.client.post(
            reverse("system:materials-checkout"),
            {"selected_products_payload": payload},
        )

        orders = RegistrationOrder.objects.filter(person=person)
        self.assertEqual(orders.count(), 2)
        materials_order = orders.filter(kind=OrderKind.ONE_TIME).first()
        self.assertIsNotNone(materials_order)
        self.assertEqual(materials_order.items.count(), 1)

    def test_materials_checkout_without_session_redirects_to_register(self):
        payload = json.dumps([{"variant_id": self.variant.pk, "qty": 1}])
        response = self.client.post(
            reverse("system:materials-checkout"),
            {"selected_products_payload": payload},
        )

        self.assertRedirects(response, reverse("system:register"), fetch_redirect_response=False)

    # -----------------------------------------------------------------------
    # FinalizeRegistrationView
    # -----------------------------------------------------------------------

    def test_finalize_activates_person(self):
        self.client.post(reverse("system:register"), self._register_payload())
        person = Person.objects.get(cpf="123.456.789-01")
        session = self.client.session
        session["pending_registration_person_id"] = person.pk
        session["post_plan_payment_complete"] = True
        session.save()

        self.client.post(reverse("system:finalize-registration"))

        person.refresh_from_db()
        self.assertTrue(person.is_active)

    def test_finalize_logs_in_user_and_redirects_to_dashboard(self):
        self.client.post(reverse("system:register"), self._register_payload())
        person = Person.objects.get(cpf="123.456.789-01")
        session = self.client.session
        session["pending_registration_person_id"] = person.pk
        session["post_plan_payment_complete"] = True
        session.save()

        response = self.client.post(reverse("system:finalize-registration"))

        self.assertRedirects(
            response,
            reverse("system:dashboard-redirect"),
            fetch_redirect_response=False,
        )
        self.assertIn(PORTAL_ACCOUNT_SESSION_KEY, self.client.session)

    def test_finalize_without_session_redirects_to_register(self):
        response = self.client.post(reverse("system:finalize-registration"))

        self.assertRedirects(response, reverse("system:register"), fetch_redirect_response=False)

    def test_finalize_clears_pending_session_keys(self):
        self.client.post(reverse("system:register"), self._register_payload())
        person = Person.objects.get(cpf="123.456.789-01")
        session = self.client.session
        session["pending_registration_person_id"] = person.pk
        session["post_plan_payment_complete"] = True
        session.save()

        self.client.post(reverse("system:finalize-registration"))

        self.assertNotIn("pending_registration_person_id", self.client.session)
        self.assertNotIn("post_plan_payment_complete", self.client.session)
