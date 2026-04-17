from django.urls import reverse
from django.utils import timezone
from django.views.generic import RedirectView, TemplateView

from system.models.membership import MembershipInvoice
from system.services.class_calendar import get_today_classes_for_person
from system.services.membership import (
    get_active_membership,
    get_latest_open_order,
    get_membership_owner,
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
        if person_type_code == "administrative-assistant":
            return reverse("system:administrative-home")
        if person_type_code == "instructor":
            return reverse("system:instructor-home")
        return reverse("system:student-home")


class AdminHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ("administrative-assistant",)
    template_name = "home/admin/dashboard.html"


class AdministrativeHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ("administrative-assistant",)
    template_name = "home/administrative/dashboard.html"


class InstructorHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ("instructor",)
    template_name = "home/instructor/dashboard.html"


class StudentHomeView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ("student", "guardian", "dependent")
    template_name = "home/student/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = getattr(self.request, "portal_person", None)
        if person:
            context["today_classes"] = get_today_classes_for_person(person)
            billing_owner = get_membership_owner(person)
            active_membership = get_active_membership(person)
            context["active_membership"] = active_membership
            context["pending_order"] = get_latest_open_order(person)
            context["billing_owner"] = billing_owner
            context["active_trial_access"] = get_active_trial_for_person(person)
            if active_membership is not None:
                context["recent_invoices"] = list(
                    MembershipInvoice.objects.filter(membership=active_membership)
                    .order_by("-paid_at", "-created_at")[:5]
                )
            else:
                context["recent_invoices"] = []
        else:
            context["today_classes"] = []
            context["active_membership"] = None
            context["pending_order"] = None
            context["billing_owner"] = None
            context["active_trial_access"] = None
            context["recent_invoices"] = []
        today = timezone.localdate()
        weekdays_pt = {
            0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
            3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo",
        }
        context["today_weekday"] = weekdays_pt.get(today.weekday(), "")
        context["today_date"] = today.strftime("%d/%m/%Y")
        return context
