from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_codes: tuple[str, ...] = ()
    allow_staff = False
    allow_superuser = False

    def test_func(self):
        user = self.request.user
        if self.allow_superuser and user.is_superuser:
            return True
        if self.allow_staff and user.is_staff:
            return True
        if not hasattr(user, "person_profile"):
            return False
        return user.person_profile.person_types.filter(
            code__in=self.allowed_codes
        ).exists()


class RootRedirectView(RedirectView):
    pattern_name = "system:dashboard-redirect"


class DashboardRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return reverse("system:admin-home")

        if user.is_staff and not hasattr(user, "person_profile"):
            return reverse("system:administrative-home")

        person = getattr(user, "person_profile", None)
        if person is None:
            return reverse("system:student-home")

        type_codes = set(
            person.person_types.values_list("code", flat=True)
        )

        if "administrative_assistant" in type_codes:
            return reverse("system:administrative-home")
        if "instructor" in type_codes:
            return reverse("system:instructor-home")
        return reverse("system:student-home")


class AdminHomeView(RoleRequiredMixin, TemplateView):
    allow_superuser = True
    template_name = "home/admin/dashboard.html"


class AdministrativeHomeView(RoleRequiredMixin, TemplateView):
    allowed_codes = ("administrative_assistant",)
    allow_staff = True
    allow_superuser = True
    template_name = "home/administrative/dashboard.html"


class InstructorHomeView(RoleRequiredMixin, TemplateView):
    allowed_codes = ("instructor",)
    allow_superuser = True
    template_name = "home/instructor/dashboard.html"


class StudentHomeView(RoleRequiredMixin, TemplateView):
    allowed_codes = ("student", "guardian")
    allow_staff = True
    allow_superuser = True
    template_name = "home/student/dashboard.html"
