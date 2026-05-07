from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import RedirectView, TemplateView

from system.constants import (
    ADMINISTRATIVE_PERSON_TYPE_CODES,
    INSTRUCTOR_PERSON_TYPE_CODES,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
    PersonTypeCode,
)
from system.models.membership import MembershipInvoice
from system.services.class_calendar import (
    get_instructor_checkin_history,
    get_student_checkin_history,
    get_today_classes_for_instructor,
    get_today_classes_for_person,
)
from system.services.graduation import (
    compute_graduation_progress,
    get_graduation_history,
)
from system.services.membership import (
    get_active_membership,
    get_guardian_billing_tabs,
    get_latest_open_order,
    get_membership_owner,
    has_dependents,
)
from system.services.trial_access import get_active_trial_for_person
from system.views.portal_mixins import PortalLoginRequiredMixin, PortalRoleRequiredMixin


class RootRedirectView(RedirectView):
    pattern_name = "system:dashboard-redirect"


class DashboardRedirectView(PortalLoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.portal_is_technical_admin:
            return reverse("system:admin-home")
        if self.request.portal_person is None:
            return reverse("system:login")
        person_type_code = next(iter(self.request.portal_type_codes), "")
        if person_type_code == PersonTypeCode.ADMINISTRATIVE_ASSISTANT:
            return reverse("system:administrative-home")
        if person_type_code == PersonTypeCode.INSTRUCTOR:
            return reverse("system:instructor-home")
        return reverse("system:student-home")


class TechnicalAdminRequiredMixin(PortalLoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "portal_is_technical_admin", False):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminHomeView(TechnicalAdminRequiredMixin, TemplateView):
    template_name = "home/admin/dashboard.html"


class StaffDashboardContextMixin:
    dashboard_page_title = "Painel do professor | LV JIU JITSU"
    dashboard_eyebrow = "Área do professor"
    dashboard_title = "Painel do professor"
    show_administrative_area = False
    show_operational_area = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = getattr(self.request, "portal_person", None)
        if person:
            context["today_classes"] = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
            context["graduation_progress"] = compute_graduation_progress(person)
            context["graduation_history"] = get_graduation_history(person)
        else:
            context["today_classes"] = []
            context["attendance_history"] = []
            context["graduation_progress"] = None
            context["graduation_history"] = []
        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        context["today_iso"] = today.strftime("%Y-%m-%d")
        context["special_class_default_title"] = settings.SPECIAL_CLASS_DEFAULT_TITLE
        context["special_class_default_duration_minutes"] = (
            settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES
        )
        context["dashboard_page_title"] = self.dashboard_page_title
        context["dashboard_eyebrow"] = self.dashboard_eyebrow
        context["dashboard_title"] = self.dashboard_title
        context["show_administrative_area"] = self.show_administrative_area
        context["show_operational_area"] = self.show_operational_area
        context["show_financial_button"] = True
        context["show_back_button"] = False
        return context


class AdministrativeHomeView(
    StaffDashboardContextMixin,
    PortalRoleRequiredMixin,
    TemplateView,
):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES
    template_name = "home/instructor/dashboard.html"
    dashboard_page_title = "Painel administrativo | LV JIU JITSU"
    dashboard_eyebrow = "Área administrativa"
    dashboard_title = "Painel administrativo"
    show_administrative_area = True


class InstructorHomeView(StaffDashboardContextMixin, PortalRoleRequiredMixin, TemplateView):
    allowed_codes = INSTRUCTOR_PERSON_TYPE_CODES
    template_name = "home/instructor/dashboard.html"
    show_operational_area = True


class StudentHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES
    template_name = "home/student/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = getattr(self.request, "portal_person", None)
        if person:
            context["today_classes"] = get_today_classes_for_person(person)
            context["attendance_history"] = get_student_checkin_history(person)
            context["active_trial_access"] = get_active_trial_for_person(person)
            context["graduation_progress"] = compute_graduation_progress(person)
            context["graduation_history"] = get_graduation_history(person)

            if has_dependents(person):
                context["billing_tabs"] = get_guardian_billing_tabs(person)
            else:
                billing_owner = get_membership_owner(person)
                active_membership = get_active_membership(person)
                pending_order = get_latest_open_order(person)
                recent_invoices = []
                if active_membership is not None:
                    recent_invoices = list(
                        MembershipInvoice.objects.filter(membership=active_membership)
                        .order_by("-paid_at", "-created_at")[:5]
                    )
                context["billing_tabs"] = [{
                    "person": person,
                    "active_membership": active_membership,
                    "pending_order": pending_order,
                    "recent_invoices": recent_invoices,
                    "is_active_tab": True,
                    "billing_owner": billing_owner,
                }]
        else:
            context["today_classes"] = []
            context["attendance_history"] = []
            context["billing_tabs"] = []
            context["active_trial_access"] = None
            context["graduation_progress"] = None
            context["graduation_history"] = []
        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        return context
