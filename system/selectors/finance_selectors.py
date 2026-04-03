from decimal import Decimal

from django.db.models import Prefetch, Q
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
    SubscriptionStudent,
)


def get_active_financial_plans():
    today = timezone.localdate()
    queryset = FinancialPlan.objects.filter(is_active=True, active_from__lte=today).filter(
        Q(active_until__isnull=True) | Q(active_until__gte=today)
    )
    return queryset.order_by("name")


def get_financial_plans_queryset():
    return FinancialPlan.objects.order_by("name")


def get_financial_benefits_queryset():
    return FinancialBenefit.objects.order_by("name")


def get_subscriptions_queryset():
    covered_students = SubscriptionStudent.objects.select_related("student", "student__user", "student_benefit")
    return LocalSubscription.objects.select_related("plan", "responsible_user", "benefit").prefetch_related(
        Prefetch("covered_students", queryset=covered_students.order_by("student__user__full_name"))
    )


def get_invoices_queryset():
    return MonthlyInvoice.objects.select_related(
        "subscription",
        "subscription__responsible_user",
        "subscription__plan",
    ).prefetch_related("payment_proofs")


def get_pauses_queryset():
    return EnrollmentPause.objects.select_related("student__user", "subscription")


def get_payment_proofs_queryset():
    return PaymentProof.objects.select_related(
        "invoice",
        "invoice__subscription",
        "invoice__subscription__responsible_user",
        "invoice__subscription__plan",
        "uploaded_by",
        "reviewed_by",
    )


def get_responsible_invoices_queryset(user):
    return get_invoices_queryset().filter(subscription__responsible_user=user)


def get_pdv_products_queryset():
    return PdvProduct.objects.order_by("display_order", "name")


def get_cash_sessions_queryset():
    return CashSession.objects.select_related("operator_user", "opened_by", "closed_by").order_by("-opened_at")


def get_recent_pdv_sales_queryset():
    return PdvSale.objects.select_related(
        "cash_session",
        "operator_user",
        "customer_student__user",
    ).prefetch_related("items", "cash_movements")


def get_cash_movements_queryset():
    return CashMovement.objects.select_related(
        "cash_session",
        "cash_session__operator_user",
        "sale",
        "created_by",
    ).order_by("-created_at")


def get_open_cash_session_for_user(user):
    return get_cash_sessions_queryset().filter(operator_user=user, status=CashSession.STATUS_OPEN).first()


def build_cash_closure_summary(cash_session):
    movements = cash_session.movements.all()
    expected_cash_total = Decimal("0.00")
    total_cash_in = Decimal("0.00")
    total_cash_out = Decimal("0.00")
    total_non_cash = Decimal("0.00")
    for movement in movements:
        if movement.payment_method == PdvSale.PAYMENT_CASH:
            if movement.direction == CashMovement.DIRECTION_IN:
                total_cash_in += movement.amount
                expected_cash_total += movement.amount
            else:
                total_cash_out += movement.amount
                expected_cash_total -= movement.amount
        elif movement.direction == CashMovement.DIRECTION_IN:
            total_non_cash += movement.amount
    return {
        "expected_cash_total": expected_cash_total,
        "total_cash_in": total_cash_in,
        "total_cash_out": total_cash_out,
        "total_non_cash": total_non_cash,
        "sales_count": cash_session.sales.count(),
    }
