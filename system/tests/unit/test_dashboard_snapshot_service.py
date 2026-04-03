import pytest
from django.utils import timezone

from system.models import MonthlyInvoice
from system.services.dashboard import get_or_create_dashboard_daily_snapshot
from system.tests.factories.attendance_factories import PhysicalAttendanceFactory
from system.tests.factories.finance_factories import (
    EnrollmentPauseFactory,
    LocalSubscriptionFactory,
    MonthlyInvoiceFactory,
    PaymentProofFactory,
)
from system.tests.factories.payments_factories import CheckoutRequestFactory
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_dashboard_snapshot_service_aggregates_core_kpis():
    active_student = StudentProfileFactory()
    pending_student = StudentProfileFactory(operational_status="PENDING_FINANCIAL")
    paid_invoice = MonthlyInvoiceFactory(status=MonthlyInvoice.STATUS_PAID)
    paid_invoice.paid_at = timezone.now()
    paid_invoice.save(update_fields=["paid_at", "updated_at"])
    MonthlyInvoiceFactory(status=MonthlyInvoice.STATUS_OVERDUE)
    PaymentProofFactory(status="UNDER_REVIEW")
    PhysicalAttendanceFactory(student=active_student)
    EnrollmentPauseFactory(student=pending_student)
    checkout_request = CheckoutRequestFactory(status="SESSION_CREATED")
    checkout_request.local_subscription.status = checkout_request.local_subscription.STATUS_CANCELLED
    checkout_request.local_subscription.end_date = timezone.localdate()
    checkout_request.local_subscription.save(update_fields=["status", "end_date", "updated_at"])

    snapshot = get_or_create_dashboard_daily_snapshot()

    assert snapshot.active_students_count >= 2
    assert snapshot.pending_financial_students_count >= 1
    assert snapshot.paid_revenue_total >= paid_invoice.amount_net
    assert snapshot.attendances_count >= 1
    assert snapshot.overdue_invoices_count >= 1
    assert snapshot.under_review_proofs_count >= 1
    assert snapshot.active_pauses_count >= 1
    assert snapshot.pending_checkout_requests_count >= 1
    assert snapshot.cancelled_subscriptions_count >= 1
