from datetime import date, datetime
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    IbjjfAgeCategory,
    Person,
    PersonType,
    RegistrationOrder,
    SubscriptionPlan,
    TeacherPayrollConfig,
)
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.models.registration_order import PaymentProvider, PaymentStatus
from system.services.payroll_rules import (
    PAYROLL_METHOD_STUDENT_PERCENTAGE,
    calculate_monthly_payroll,
    encode_payroll_rules,
)

ORDER_COUNT = 12


class PayrollBatchQueryBudgetTestCase(TestCase):
    MAX_QUERIES_WITH_MANY_ORDERS = 28

    @classmethod
    def setUpTestData(cls):
        cls.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        cls.teacher_type = PersonType.objects.create(code="instructor", display_name="Professor")
        cls.category = ClassCategory.objects.create(
            code="payroll-perf",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-payroll-perf",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            maximum_age=99,
        )
        cls.teacher = Person.objects.create(
            full_name="Prof. Payroll Perf",
            cpf="811.000.000-00",
            person_type=cls.teacher_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        cls.group = ClassGroup.objects.create(
            display_name="Turma Payroll Perf",
            class_category=cls.category,
            main_teacher=cls.teacher,
        )
        cls.plan = SubscriptionPlan.objects.create(
            code="payroll-perf-plan",
            display_name="Plano Payroll Perf",
            price=Decimal("200.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
        )
        TeacherPayrollConfig.objects.create(
            person=cls.teacher,
            monthly_salary=Decimal("0.00"),
            payment_day=28,
            notes=encode_payroll_rules(
                [
                    {
                        "method": PAYROLL_METHOD_STUDENT_PERCENTAGE,
                        "percentage": "50.00",
                        "scope": "class_group",
                        "class_group_id": cls.group.pk,
                    },
                ]
            ),
        )

        cpfs = [
            "39053344705",
            "52998224725",
            "74412652823",
            "60734327042",
            "12345678909",
            "98765432100",
            "11144477735",
            "22255588846",
            "33366699957",
            "44477700068",
            "55588811179",
            "66699922280",
        ]
        for index in range(ORDER_COUNT):
            student = Person.objects.create(
                full_name=f"Aluno Payroll {index}",
                cpf=cpfs[index],
                person_type=cls.student_type,
                birth_date=date(2000, 1, 1),
                biological_sex=BiologicalSex.MALE,
            )
            ClassEnrollment.objects.create(class_group=cls.group, person=student)
            RegistrationOrder.objects.create(
                person=student,
                plan=cls.plan,
                plan_price=Decimal("200.00"),
                total=Decimal("200.00"),
                payment_status=PaymentStatus.PAID,
                payment_provider=PaymentProvider.ASAAS,
                net_amount=Decimal("198.00"),
                paid_at=timezone.make_aware(datetime(2026, 4, 5 + (index % 20), 10, 0)),
            )

    def test_calculate_monthly_payroll_scales_without_per_order_n_plus_one(self):
        with CaptureQueriesContext(connection) as context:
            result = calculate_monthly_payroll(
                self.teacher,
                reference_month=date(2026, 4, 1),
            )

        self.assertLessEqual(len(context.captured_queries), self.MAX_QUERIES_WITH_MANY_ORDERS)
        self.assertEqual(result["student_count"], ORDER_COUNT)
        self.assertGreater(result["student_total"], Decimal("0.00"))
