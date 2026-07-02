from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Person, PersonType
from system.models.registration_order import OrderKind, PaymentStatus, RegistrationOrder
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationFinancialRoutesTestCase(TestCase):
    """PRD-077: rotas canonicas em ingles para Financeiro (telas de leitura + acao)."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-financial",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.student = Person.objects.create(
            full_name="Aluno Fundacao Financeiro",
            cpf="777.777.777-77",
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
        )
        self.pending_order = RegistrationOrder.objects.create(
            person=self.student,
            total="150.00",
            kind=OrderKind.ONE_TIME,
            payment_status=PaymentStatus.PENDING,
        )
        self._login_technical_admin()

    def test_english_financial_control_route_renders(self):
        response = self.client.get(reverse("system:financial-control"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/financial/")

    def test_old_portuguese_route_redirects_to_english(self):
        response = self.client.get("/financeiro/")
        self.assertRedirects(response, reverse("system:financial-control"))

    def test_english_pending_payments_route_renders(self):
        response = self.client.get(reverse("system:pending-payments"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/financial/pending/")
        self.assertContains(response, "Aluno Fundacao Financeiro")

    def test_mark_order_paid_action_updates_status(self):
        response = self.client.post(
            reverse("system:mark-order-paid", kwargs={"order_id": self.pending_order.pk}),
        )
        self.assertRedirects(response, reverse("system:pending-payments"))
        self.pending_order.refresh_from_db()
        self.assertEqual(self.pending_order.payment_status, PaymentStatus.PAID)

    def test_english_payroll_and_payout_routes_render(self):
        payroll_response = self.client.get(reverse("system:payroll-list"))
        payout_response = self.client.get(reverse("system:payout-queue"))
        self.assertEqual(payroll_response.status_code, 200)
        self.assertEqual(payout_response.status_code, 200)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
