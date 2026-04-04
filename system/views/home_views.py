from django.urls import reverse
from django.views.generic import RedirectView, TemplateView

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
        if "administrative-assistant" in self.request.portal_type_codes:
            return reverse("system:administrative-home")
        if "instructor" in self.request.portal_type_codes:
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
