from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_PROFESSOR, ROLE_RECEPCAO
from system.mixins import RoleRequiredMixin
from system.models import LocalSubscription, MonthlyInvoice
from system.selectors import (
    get_admin_dashboard_pending_items,
    get_dashboard_visible_students_for_user,
    get_recent_attendances_for_student,
    get_responsible_invoices_queryset,
    get_responsible_subscriptions_for_user,
    get_self_service_sessions_for_student,
    get_student_dashboard_selected_student,
)
from system.services.dashboard import get_or_create_dashboard_daily_snapshot


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class PortalDashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.has_any_role(*ADMIN_ROLE_CODES):
            return redirect("system:admin-dashboard")
        if _has_student_or_household_context(request.user):
            return redirect("system:student-dashboard")
        if request.user.has_role(ROLE_PROFESSOR):
            return redirect("system:professor-dashboard")
        return redirect("system:my-profile")


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "system/dashboard/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible_students = list(get_dashboard_visible_students_for_user(self.request.user))
        selected_student = get_student_dashboard_selected_student(
            user=self.request.user,
            student_uuid=self.request.GET.get("student_uuid"),
        )
        responsible_subscriptions = list(get_responsible_subscriptions_for_user(self.request.user))
        can_view_finance = bool(responsible_subscriptions)
        self_service_student = _resolve_self_service_student(self.request.user, selected_student)
        invoices = list(get_responsible_invoices_queryset(self.request.user)[:8]) if can_view_finance else []
        recent_attendances = list(get_recent_attendances_for_student(self_service_student)[:5])
        self_service_sessions = list(get_self_service_sessions_for_student(self_service_student)[:5])
        context.update(
            {
                "visible_students": visible_students,
                "selected_student": selected_student,
                "responsible_subscriptions": responsible_subscriptions,
                "can_view_finance": can_view_finance,
                "invoices": invoices,
                "needs_regularization": _needs_regularization(responsible_subscriptions, invoices),
                "regularization_url": reverse("system:my-invoices"),
                "self_service_student": self_service_student,
                "self_service_sessions": self_service_sessions,
                "recent_attendances": recent_attendances,
            }
        )
        return context


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "system/dashboard/admin_dashboard.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reference_date = _get_reference_date_from_request(self.request)
        snapshot = get_or_create_dashboard_daily_snapshot(reference_date=reference_date)
        context["snapshot"] = snapshot
        context["pending_items"] = get_admin_dashboard_pending_items()
        context["selected_month"] = snapshot.snapshot_date.strftime("%Y-%m")
        context["shortcuts"] = (
            ("Financeiro", reverse("system:finance-dashboard")),
            ("Pagamentos Stripe", reverse("system:payment-dashboard")),
            ("Relatorios e auditoria", reverse("system:report-center")),
            ("Alunos", reverse("system:student-list")),
            ("Turmas e sessoes", reverse("system:session-list")),
            ("Professores", reverse("system:instructor-list")),
            ("Graduacao", reverse("system:graduation-panel")),
        )
        return context


def _has_student_or_household_context(user):
    return get_dashboard_visible_students_for_user(user).exists() or get_responsible_subscriptions_for_user(user).exists()


def _resolve_self_service_student(user, selected_student):
    if selected_student is None:
        return None
    if selected_student.user_id != user.id:
        return None
    if not selected_student.self_service_access:
        return None
    return selected_student


def _needs_regularization(subscriptions, invoices):
    pending_invoice_statuses = {
        MonthlyInvoice.STATUS_OVERDUE,
        MonthlyInvoice.STATUS_UNDER_REVIEW,
    }
    if any(subscription.status == LocalSubscription.STATUS_PENDING_FINANCIAL for subscription in subscriptions):
        return True
    return any(invoice.status in pending_invoice_statuses for invoice in invoices)


def _get_reference_date_from_request(request):
    month_value = request.GET.get("month", "").strip()
    if not month_value:
        return timezone.localdate()
    try:
        return datetime.strptime(month_value, "%Y-%m").date().replace(day=1)
    except ValueError:
        return timezone.localdate()
