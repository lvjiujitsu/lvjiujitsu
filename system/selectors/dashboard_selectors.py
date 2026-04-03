from datetime import timedelta
from decimal import Decimal

from django.db.models import Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from system.models import (
    CheckoutRequest,
    ClassReservation,
    ClassSession,
    EnrollmentPause,
    LocalSubscription,
    MonthlyInvoice,
    PaymentProof,
    PhysicalAttendance,
    StudentProfile,
    SubscriptionStudent,
    TrialClassRequest,
)
from system.selectors.finance_selectors import get_invoices_queryset, get_pauses_queryset, get_payment_proofs_queryset
from system.selectors.student_selectors import get_visible_students_for_user


def get_student_dashboard_selected_student(*, user, student_uuid=None):
    visible_students = get_visible_students_for_user(user)
    if student_uuid:
        selected = visible_students.filter(uuid=student_uuid).first()
        if selected:
            return selected
    own_student = visible_students.filter(user=user).first()
    return own_student or visible_students.first()


def get_dashboard_visible_students_for_user(user):
    return get_visible_students_for_user(user)


def get_responsible_subscriptions_for_user(user):
    covered_students = SubscriptionStudent.objects.select_related("student", "student__user")
    invoices = MonthlyInvoice.objects.order_by("-reference_month", "-due_date")
    return (
        LocalSubscription.objects.select_related("plan", "benefit", "responsible_user", "stripe_subscription_link")
        .prefetch_related(
            Prefetch("covered_students", queryset=covered_students.order_by("student__user__full_name")),
            Prefetch("invoices", queryset=invoices),
            "checkout_requests",
        )
        .filter(responsible_user=user)
        .order_by("-created_at")
    )


def get_self_service_sessions_for_student(student):
    if student is None:
        return ClassSession.objects.none()
    now = timezone.now()
    future_window = now + timedelta(days=7)
    return (
        ClassSession.objects.select_related("class_group", "class_group__modality")
        .filter(
            Q(
                reservations__student=student,
                reservations__status=ClassReservation.STATUS_ACTIVE,
                starts_at__gte=now - timedelta(hours=1),
            )
            | Q(
                reservations__student=student,
                reservations__status=ClassReservation.STATUS_CONSUMED,
                starts_at__gte=now - timedelta(hours=2),
            )
            | Q(
                class_group__reservation_required=False,
                status=ClassSession.STATUS_OPEN,
                starts_at__lte=now,
                ends_at__gte=now,
            )
        )
        .filter(starts_at__lte=future_window)
        .distinct()
        .order_by("starts_at")
    )


def get_recent_attendances_for_student(student):
    if student is None:
        return PhysicalAttendance.objects.none()
    return (
        PhysicalAttendance.objects.select_related("session", "session__class_group", "session__class_group__modality")
        .filter(student=student)
        .order_by("-checked_in_at")
    )


def get_admin_dashboard_pending_items(limit=8):
    return {
        "overdue_invoices": get_invoices_queryset().filter(status=MonthlyInvoice.STATUS_OVERDUE)[:limit],
        "proofs_under_review": get_payment_proofs_queryset().filter(status=PaymentProof.STATUS_UNDER_REVIEW)[:limit],
        "active_pauses": get_pauses_queryset().filter(is_active=True)[:limit],
        "requested_trials": TrialClassRequest.objects.select_related("lead").filter(
            status=TrialClassRequest.STATUS_REQUESTED
        )[:limit],
        "pending_checkouts": (
            CheckoutRequest.objects.select_related("local_subscription", "local_subscription__responsible_user")
            .filter(status__in=(CheckoutRequest.STATUS_CREATED, CheckoutRequest.STATUS_SESSION_CREATED))
            .order_by("-created_at")[:limit]
        ),
    }


def build_admin_dashboard_metrics(*, reference_date=None):
    today = reference_date or timezone.localdate()
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    students = StudentProfile.objects
    invoices = MonthlyInvoice.objects
    attendances = PhysicalAttendance.objects
    subscriptions = LocalSubscription.objects
    return {
        "snapshot_date": today,
        "active_students_count": students.filter(is_active=True).exclude(
            operational_status=StudentProfile.STATUS_INACTIVE
        ).count(),
        "pending_financial_students_count": students.filter(
            operational_status=StudentProfile.STATUS_PENDING_FINANCIAL
        ).count(),
        "paid_revenue_total": invoices.filter(
            status=MonthlyInvoice.STATUS_PAID,
            paid_at__date__gte=month_start,
            paid_at__date__lt=next_month,
        ).aggregate(total=Coalesce(Sum("amount_net"), Decimal("0.00")))["total"],
        "attendances_count": attendances.filter(
            checked_in_at__date__gte=month_start,
            checked_in_at__date__lt=next_month,
        ).count(),
        "cancelled_subscriptions_count": subscriptions.filter(
            status=LocalSubscription.STATUS_CANCELLED,
            end_date__gte=month_start,
            end_date__lt=next_month,
        ).count(),
        "active_pauses_count": EnrollmentPause.objects.filter(is_active=True).count(),
        "overdue_invoices_count": invoices.filter(status=MonthlyInvoice.STATUS_OVERDUE).count(),
        "under_review_proofs_count": PaymentProof.objects.filter(status=PaymentProof.STATUS_UNDER_REVIEW).count(),
        "requested_trial_classes_count": TrialClassRequest.objects.filter(
            status=TrialClassRequest.STATUS_REQUESTED
        ).count(),
        "pending_checkout_requests_count": CheckoutRequest.objects.filter(
            status__in=(CheckoutRequest.STATUS_CREATED, CheckoutRequest.STATUS_SESSION_CREATED)
        ).count(),
        "metadata": {
            "month_start": month_start.isoformat(),
        },
    }
