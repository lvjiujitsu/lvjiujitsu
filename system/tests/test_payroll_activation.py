from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from system.constants import PersonTypeCode
from system.models import (
    CategoryAudience,
    ClassCategory,
    Person,
    PersonType,
    TeacherPayrollConfig,
)
from system.services.class_requests import (
    approve_class_catalog_request,
    create_new_teacher_class_request,
)
from system.services.payroll_activation import (
    activate_payroll_from_class_request,
    can_activate_payroll_from_request,
)


class PayrollActivationServiceTestCase(TestCase):
    def setUp(self):
        self.instructor_type = PersonType.objects.create(
            code=PersonTypeCode.INSTRUCTOR,
            display_name="Professor",
        )
        self.admin_type = PersonType.objects.create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            display_name="Administrativo",
        )
        self.category = ClassCategory.objects.create(
            code="adult-payroll-activation",
            display_name="Adulto Repasse",
            audience=CategoryAudience.ADULT,
        )
        self.approver_person = Person.objects.create(
            full_name="Gestor Repasse",
            cpf="500.000.000-03",
            person_type=self.admin_type,
            birth_date=date(1980, 1, 1),
        )

    def _create_paid_teacher_request(self):
        return create_new_teacher_class_request(
            full_name="Professor Repasse",
            cpf="93541134780",
            email="professor.payroll@example.com",
            phone="11970000020",
            password="Teste@12345",
            class_category=self.category,
            display_name="Turma Repasse",
            weekday="monday",
            training_style="mixed",
            start_time=time(19, 0),
            duration_minutes=60,
            default_capacity=20,
            justification="Proposta com repasse fixo.",
            payout_data={
                "method": "pix",
                "pix_key_type": "CPF",
                "pix_key": "935.411.347-80",
                "holder_name": "Professor Repasse",
                "holder_document": "935.411.347-80",
                "financial_arrangement": "paid_fixed",
                "fixed_amount": "300.00",
            },
        )

    def test_approval_does_not_create_payroll_config(self):
        request = self._create_paid_teacher_request()
        approve_class_catalog_request(request.pk, approved_by=self.approver_person)
        request.refresh_from_db()
        self.assertTrue(can_activate_payroll_from_request(request))
        teacher = request.created_teacher
        self.assertFalse(TeacherPayrollConfig.objects.filter(person=teacher, is_active=True).exists())

    def test_activate_payroll_from_approved_request(self):
        request = self._create_paid_teacher_request()
        approve_class_catalog_request(request.pk, approved_by=self.approver_person)
        request.refresh_from_db()
        self.assertTrue(can_activate_payroll_from_request(request))

        config = activate_payroll_from_class_request(
            request,
            activated_by=self.approver_person,
            payment_day=10,
            decision_notes="Ativação homologada.",
        )

        self.assertTrue(config.is_active)
        self.assertEqual(config.payment_day, 10)
        request.refresh_from_db()
        self.assertIn("payroll_activation", request.payload)
        self.assertFalse(can_activate_payroll_from_request(request))

    def test_activate_payroll_is_idempotent_for_same_teacher(self):
        request = self._create_paid_teacher_request()
        approve_class_catalog_request(request.pk, approved_by=self.approver_person)
        request.refresh_from_db()
        activate_payroll_from_class_request(
            request,
            activated_by=self.approver_person,
            payment_day=5,
        )
        with self.assertRaises(ValidationError):
            activate_payroll_from_class_request(
                request,
                activated_by=self.approver_person,
                payment_day=7,
            )
