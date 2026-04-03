from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from system.models import (
    CashMovement,
    CashSession,
    EnrollmentPause,
    FinancialBenefit,
    FinancialPlan,
    LocalSubscription,
    MonthlyInvoice,
    PaymentProof,
    PdvProduct,
    PdvSale,
    PdvSaleItem,
    SubscriptionStudent,
)
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.student_factories import StudentProfileFactory


class FinancialPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FinancialPlan

    name = factory.Sequence(lambda index: f"Plano {index}")
    slug = factory.Sequence(lambda index: f"plano-{index}")
    billing_cycle = FinancialPlan.CYCLE_MONTHLY
    base_price = Decimal("250.00")
    is_active = True


class FinancialBenefitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FinancialBenefit

    name = factory.Sequence(lambda index: f"Beneficio {index}")
    benefit_type = FinancialBenefit.TYPE_DISCOUNT
    value_type = FinancialBenefit.VALUE_PERCENTAGE
    value = Decimal("10.00")
    is_active = True


class LocalSubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocalSubscription

    plan = factory.SubFactory(FinancialPlanFactory)
    responsible_user = factory.SubFactory(SystemUserFactory)
    status = LocalSubscription.STATUS_ACTIVE
    start_date = factory.LazyFunction(timezone.localdate)


class SubscriptionStudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubscriptionStudent

    subscription = factory.SubFactory(LocalSubscriptionFactory)
    student = factory.SubFactory(StudentProfileFactory)
    is_primary_student = True
    is_active = True


class MonthlyInvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MonthlyInvoice

    subscription = factory.SubFactory(LocalSubscriptionFactory)
    reference_month = factory.LazyFunction(lambda: timezone.localdate().replace(day=1))
    due_date = factory.LazyFunction(lambda: timezone.localdate() + timedelta(days=5))
    amount_gross = Decimal("250.00")
    amount_discount = Decimal("0.00")
    amount_net = Decimal("250.00")
    status = MonthlyInvoice.STATUS_OPEN


class EnrollmentPauseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EnrollmentPause

    student = factory.SubFactory(StudentProfileFactory)
    subscription = factory.SubFactory(LocalSubscriptionFactory)
    reason = "Viagem"
    start_date = factory.LazyFunction(timezone.localdate)
    expected_return_date = factory.LazyFunction(lambda: timezone.localdate() + timedelta(days=30))
    is_active = True


class PaymentProofFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentProof

    invoice = factory.SubFactory(MonthlyInvoiceFactory)
    uploaded_by = factory.SubFactory(SystemUserFactory)
    file = factory.django.FileField(filename="proof.pdf", data=b"proof-content")
    original_filename = "proof.pdf"
    status = PaymentProof.STATUS_UNDER_REVIEW


class PdvProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PdvProduct

    sku = factory.Sequence(lambda index: f"PDV-{index:04d}")
    name = factory.Sequence(lambda index: f"Produto PDV {index}")
    description = "Produto de recepcao"
    unit_price = Decimal("35.00")
    display_order = factory.Sequence(int)
    is_active = True


class CashSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashSession

    operator_user = factory.SubFactory(SystemUserFactory)
    opened_by = factory.SelfAttribute("operator_user")
    status = CashSession.STATUS_OPEN
    opening_balance = Decimal("50.00")
    expected_cash_total = Decimal("50.00")


class PdvSaleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PdvSale

    cash_session = factory.SubFactory(CashSessionFactory)
    operator_user = factory.SelfAttribute("cash_session.operator_user")
    customer_student = None
    customer_name_snapshot = ""
    receipt_code = factory.Sequence(lambda index: f"PDV-20260402-{index:06d}")
    payment_method = PdvSale.PAYMENT_CASH
    status = PdvSale.STATUS_COMPLETED
    subtotal_amount = Decimal("35.00")
    discount_amount = Decimal("0.00")
    total_amount = Decimal("35.00")
    amount_received = Decimal("40.00")
    change_amount = Decimal("5.00")


class PdvSaleItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PdvSaleItem

    sale = factory.SubFactory(PdvSaleFactory)
    product = factory.SubFactory(PdvProductFactory)
    product_name_snapshot = factory.SelfAttribute("product.name")
    unit_price = factory.SelfAttribute("product.unit_price")
    quantity = 1
    line_total = factory.LazyAttribute(lambda obj: obj.unit_price * obj.quantity)


class CashMovementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashMovement

    cash_session = factory.SubFactory(CashSessionFactory)
    sale = None
    created_by = factory.SelfAttribute("cash_session.operator_user")
    movement_type = CashMovement.TYPE_OPENING
    direction = CashMovement.DIRECTION_IN
    payment_method = PdvSale.PAYMENT_CASH
    amount = Decimal("50.00")
    description = "Movimentacao de caixa"
