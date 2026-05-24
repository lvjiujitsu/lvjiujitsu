from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import RedirectView, TemplateView

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
from system.views.portal_mixins import PortalLoginRequiredMixin


class RootRedirectView(RedirectView):
    pattern_name = "system:dashboard-redirect"


class DashboardRedirectView(PortalLoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse("system:home")


class HomeView(PortalLoginRequiredMixin, TemplateView):
    template_name = "home/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        person = getattr(request, "portal_person", None)

        is_admin = getattr(request, "portal_is_technical_admin", False)
        is_administrative = getattr(request, "portal_is_administrative", False)
        is_instructor = getattr(request, "portal_is_instructor", False)
        is_student = getattr(request, "portal_is_student", False)

        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        context["today_iso"] = today.strftime("%Y-%m-%d")

        context["is_admin"] = is_admin
        context["is_administrative"] = is_administrative
        context["is_instructor"] = is_instructor
        context["is_student"] = is_student
        context["show_staff_area"] = is_admin or is_administrative
        context["show_instructor_area"] = is_admin or is_instructor

        if person is None:
            context.update(_empty_context())
            return context

        if is_admin or is_administrative or is_instructor:
            context["today_classes"] = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        else:
            context["today_classes"] = get_today_classes_for_person(person)
            context["attendance_history"] = get_student_checkin_history(person)

        context["graduation_progress"] = compute_graduation_progress(person)
        context["graduation_history"] = get_graduation_history(person)

        if is_student:
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
            context["active_trial_access"] = None
            context["billing_tabs"] = []

        return context


def _empty_context():
    return {
        "today_classes": [],
        "attendance_history": [],
        "graduation_progress": None,
        "graduation_history": [],
        "active_trial_access": None,
        "billing_tabs": [],
    }
