from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from system.models import FinancialBenefit, LocalSubscription, MonthlyInvoice, StudentProfile
from system.selectors.finance_selectors import get_active_financial_plans
from system.services.attendance.workflow import build_precheck_result
from system.services.finance import (
    create_enrollment_pause,
    create_local_subscription,
    issue_monthly_invoice,
    review_payment_proof,
    resume_enrollment_pause,
    sync_subscription_status,
    upload_payment_proof,
)
from system.tests.factories.class_factories import ClassSessionFactory
from system.tests.factories.finance_factories import (
    FinancialBenefitFactory,
    FinancialPlanFactory,
    LocalSubscriptionFactory,
    MonthlyInvoiceFactory,
    SubscriptionStudentFactory,
)
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_active_financial_plans_selector_respects_status_and_date_window():
    active_plan = FinancialPlanFactory()
    FinancialPlanFactory(is_active=False, slug="inactive-plan")
    FinancialPlanFactory(
        slug="future-plan",
        active_from=timezone.localdate() + timedelta(days=10),
    )

    plans = list(get_active_financial_plans())

    assert plans == [active_plan]


@pytest.mark.django_db
def test_financial_benefit_calculates_percentage_and_fixed_discount():
    percentage_benefit = FinancialBenefitFactory(value_type=FinancialBenefit.VALUE_PERCENTAGE, value=Decimal("15"))
    fixed_benefit = FinancialBenefitFactory(value_type=FinancialBenefit.VALUE_FIXED, value=Decimal("50"))

    assert percentage_benefit.calculate_discount(Decimal("200.00")) == Decimal("30.00")
    assert fixed_benefit.calculate_discount(Decimal("40.00")) == Decimal("40.00")


@pytest.mark.django_db
def test_create_local_subscription_supports_financial_responsible_without_training():
    holder = StudentProfileFactory(student_type=StudentProfile.TYPE_HOLDER)
    dependent = StudentProfileFactory(student_type=StudentProfile.TYPE_DEPENDENT)
    plan = FinancialPlanFactory()
    benefit = FinancialBenefitFactory()

    subscription = create_local_subscription(
        plan=plan,
        responsible_cpf="99988877766",
        responsible_full_name="Responsavel Financeiro",
        responsible_email="financeiro@example.com",
        student_profiles=[holder, dependent],
        benefit=benefit,
        primary_student=holder,
    )

    covered_cpf_values = list(subscription.covered_students.values_list("student__user__cpf", flat=True))

    assert subscription.responsible_user.cpf == "99988877766"
    assert subscription.responsible_user.has_role("RESPONSAVEL_FINANCEIRO") is True
    assert len(covered_cpf_values) == 2
    assert subscription.status == LocalSubscription.STATUS_ACTIVE


@pytest.mark.django_db
def test_overdue_invoice_marks_student_as_pending_financial_and_blocks_precheck():
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    subscription = LocalSubscriptionFactory(plan=FinancialPlanFactory(blocks_checkin_on_overdue=True), responsible_user=student.user)
    SubscriptionStudentFactory(subscription=subscription, student=student)
    invoice = MonthlyInvoiceFactory(
        subscription=subscription,
        due_date=timezone.localdate() - timedelta(days=1),
        status=MonthlyInvoice.STATUS_OVERDUE,
    )
    session = ClassSessionFactory(
        status=ClassSessionFactory._meta.model.STATUS_OPEN,
        starts_at=timezone.now() - timedelta(minutes=5),
        ends_at=timezone.now() + timedelta(minutes=30),
        class_group__reservation_required=False,
    )

    sync_subscription_status(subscription)
    student.refresh_from_db()
    precheck = build_precheck_result(student=student, session=session)

    assert invoice.status == MonthlyInvoice.STATUS_OVERDUE
    assert student.operational_status == StudentProfile.STATUS_PENDING_FINANCIAL
    assert precheck["allowed"] is False
    assert precheck["reason"] == StudentProfile.STATUS_PENDING_FINANCIAL.lower()


@pytest.mark.django_db
def test_pause_and_resume_updates_student_operational_status():
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    subscription = LocalSubscriptionFactory(responsible_user=student.user)
    SubscriptionStudentFactory(subscription=subscription, student=student)

    pause = create_enrollment_pause(
        student=student,
        subscription=subscription,
        reason="Viagem internacional",
        start_date=timezone.localdate(),
        expected_return_date=timezone.localdate() + timedelta(days=15),
        notes="Pausa operacional",
    )
    student.refresh_from_db()

    assert pause.is_active is True
    assert student.operational_status == StudentProfile.STATUS_PAUSED

    resume_enrollment_pause(pause, end_date=timezone.localdate() + timedelta(days=10))
    student.refresh_from_db()

    assert student.operational_status == StudentProfile.STATUS_ACTIVE


@pytest.mark.django_db
def test_payment_proof_under_review_keeps_subscription_pending_until_approval():
    student = StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    subscription = LocalSubscriptionFactory(responsible_user=student.user)
    SubscriptionStudentFactory(subscription=subscription, student=student)
    invoice = issue_monthly_invoice(
        subscription=subscription,
        reference_month=timezone.localdate().replace(day=1),
        due_date=timezone.localdate() + timedelta(days=2),
    )
    uploaded_file = SimpleUploadedFile("proof.pdf", b"proof-content", content_type="application/pdf")

    proof = upload_payment_proof(invoice=invoice, uploaded_by=student.user, uploaded_file=uploaded_file)
    subscription.refresh_from_db()
    student.refresh_from_db()

    assert proof.status == proof.STATUS_UNDER_REVIEW
    assert invoice.status == MonthlyInvoice.STATUS_UNDER_REVIEW
    assert subscription.status == LocalSubscription.STATUS_PENDING_FINANCIAL
    assert student.operational_status == StudentProfile.STATUS_PENDING_FINANCIAL

    review_payment_proof(proof=proof, reviewer=student.user, approve=True, review_notes="Pagamento confirmado.")
    invoice.refresh_from_db()
    subscription.refresh_from_db()
    student.refresh_from_db()

    assert invoice.status == MonthlyInvoice.STATUS_PAID
    assert subscription.status == LocalSubscription.STATUS_ACTIVE
    assert student.operational_status == StudentProfile.STATUS_ACTIVE


@pytest.mark.django_db
def test_payment_proof_rejects_invalid_extension():
    student = StudentProfileFactory()
    subscription = LocalSubscriptionFactory(responsible_user=student.user)
    SubscriptionStudentFactory(subscription=subscription, student=student)
    invoice = issue_monthly_invoice(
        subscription=subscription,
        reference_month=timezone.localdate().replace(day=1),
        due_date=timezone.localdate() + timedelta(days=2),
    )
    uploaded_file = SimpleUploadedFile("proof.exe", b"proof-content", content_type="application/octet-stream")

    with pytest.raises(ValidationError):
        upload_payment_proof(invoice=invoice, uploaded_by=student.user, uploaded_file=uploaded_file)
