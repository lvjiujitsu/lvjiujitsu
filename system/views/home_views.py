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


class AdminHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES
    template_name = "home/admin/dashboard.html"


class AdministrativeHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES
    template_name = "home/administrative/dashboard.html"


class InstructorHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = INSTRUCTOR_PERSON_TYPE_CODES
    template_name = "home/instructor/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = getattr(self.request, "portal_person", None)
        if person:
            context["today_classes"] = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        else:
            context["today_classes"] = []
            context["attendance_history"] = []
        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        context["show_back_button"] = False
        return context


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
        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        return context
