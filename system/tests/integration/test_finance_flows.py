import pytest
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from system.models import FinancialBenefit, FinancialPlan, LocalSubscription, MonthlyInvoice, PaymentProof, StudentProfile
from system.tests.factories.auth_factories import AdminUserFactory, SystemUserFactory
from system.tests.factories.finance_factories import LocalSubscriptionFactory, MonthlyInvoiceFactory, SubscriptionStudentFactory
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_admin_can_create_financial_entities_and_filter_invoices(client):
    admin = AdminUserFactory()
    student = StudentProfileFactory()
    client.force_login(admin)

    plan_response = client.post(
        reverse("system:finance-dashboard"),
        data={
            "action": "plan",
            "plan-name": "Plano Premium",
            "plan-slug": "plano-premium",
            "plan-billing_cycle": "MONTHLY",
            "plan-base_price": "320.00",
            "plan-description": "Plano principal",
            "plan-allows_pause": "on",
            "plan-blocks_checkin_on_overdue": "on",
            "plan-active_from": "2026-04-01",
            "plan-is_active": "on",
        },
    )
    benefit_response = client.post(
        reverse("system:finance-dashboard"),
        data={
            "action": "benefit",
            "benefit-name": "Bolsa atleta",
            "benefit-benefit_type": "SCHOLARSHIP",
            "benefit-value_type": "PERCENTAGE",
            "benefit-value": "20.00",
            "benefit-description": "Bolsa para competidor",
            "benefit-is_active": "on",
        },
    )
    plan = FinancialPlan.objects.get(slug="plano-premium")
    benefit = FinancialBenefit.objects.get(name="Bolsa atleta")
    subscription_response = client.post(
        reverse("system:finance-dashboard"),
        data={
            "action": "subscription",
            "subscription-plan": plan.id,
            "subscription-responsible_full_name": "Titular Financeiro",
            "subscription-responsible_cpf": "12312312399",
            "subscription-responsible_email": "titular.financeiro@example.com",
            "subscription-benefit": benefit.id,
            "subscription-students": [student.id],
            "subscription-primary_student": student.id,
            "subscription-status": "ACTIVE",
            "subscription-notes": "Contrato criado pela recepcao",
        },
    )
    subscription = LocalSubscription.objects.get(responsible_user__cpf="12312312399")
    invoice_response = client.post(
        reverse("system:finance-dashboard"),
        data={
            "action": "invoice",
            "invoice-subscription": subscription.id,
            "invoice-reference_month": "2026-04-01",
            "invoice-due_date": "2026-04-10",
            "invoice-amount_gross": "320.00",
        },
    )
    invoice = MonthlyInvoice.objects.get(subscription=subscription)
    manual_overdue_response = client.post(reverse("system:invoice-mark-overdue", kwargs={"uuid": invoice.uuid}))
    invoice.refresh_from_db()
    filtered_response = client.get(
        reverse("system:finance-dashboard"),
        data={"invoice_status": MonthlyInvoice.STATUS_OVERDUE},
    )

    assert plan_response.status_code == 302
    assert benefit_response.status_code == 302
    assert subscription_response.status_code == 302
    assert invoice_response.status_code == 302
    assert manual_overdue_response.status_code == 302
    assert invoice.status == MonthlyInvoice.STATUS_OVERDUE
    assert filtered_response.status_code == 200
    assert "Plano Premium" in filtered_response.content.decode()
    assert "Titular Financeiro" in filtered_response.content.decode()


@pytest.mark.django_db
def test_admin_can_pause_and_review_payment_proof_from_self_service(client):
    admin = AdminUserFactory()
    responsible_user = SystemUserFactory(password="StrongPassword123")
    student = StudentProfileFactory(user=SystemUserFactory())
    subscription = LocalSubscriptionFactory(responsible_user=responsible_user)
    SubscriptionStudentFactory(subscription=subscription, student=student)
    invoice = MonthlyInvoiceFactory(
        subscription=subscription,
        due_date=student.join_date + timedelta(days=5),
    )
    client.force_login(admin)

    pause_response = client.post(
        reverse("system:finance-dashboard"),
        data={
            "action": "pause",
            "pause-student": student.id,
            "pause-subscription": subscription.id,
            "pause-reason": "Recuperacao medica",
            "pause-start_date": "2026-04-01",
            "pause-expected_return_date": "2026-04-20",
            "pause-notes": "Suspensao temporaria",
        },
    )
    student.refresh_from_db()

    client.force_login(responsible_user)
    upload_response = client.post(
        reverse("system:my-invoices"),
        data={
            "invoice_uuid": str(invoice.uuid),
            "uploaded_file": SimpleUploadedFile("proof.pdf", b"proof", content_type="application/pdf"),
        },
    )
    proof = PaymentProof.objects.get(invoice=invoice)

    client.force_login(admin)
    review_response = client.post(
        reverse("system:payment-proof-review", kwargs={"uuid": proof.uuid}),
        data={"decision": "approve", "review_notes": "Comprovante conferido."},
    )
    invoice.refresh_from_db()

    assert pause_response.status_code == 302
    assert student.operational_status == StudentProfile.STATUS_PAUSED
    assert upload_response.status_code == 302
    assert proof.status == PaymentProof.STATUS_UNDER_REVIEW
    assert review_response.status_code == 302
    assert invoice.status == MonthlyInvoice.STATUS_PAID


@pytest.mark.django_db
def test_non_responsible_user_cannot_upload_payment_proof_for_other_invoice(client):
    responsible_user = SystemUserFactory(password="StrongPassword123")
    other_user = SystemUserFactory(password="StrongPassword123")
    subscription = LocalSubscriptionFactory(responsible_user=responsible_user)
    invoice = MonthlyInvoiceFactory(subscription=subscription)
    client.force_login(other_user)

    response = client.post(
        reverse("system:my-invoices"),
        data={
            "invoice_uuid": str(invoice.uuid),
            "uploaded_file": SimpleUploadedFile("proof.pdf", b"proof", content_type="application/pdf"),
        },
    )

    assert response.status_code == 200
    assert "Voce nao pode enviar comprovante para esta fatura." in response.content.decode()
    assert PaymentProof.objects.count() == 0
