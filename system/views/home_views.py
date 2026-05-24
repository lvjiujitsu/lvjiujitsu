from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import RedirectView, TemplateView

from system.models.asaas import TeacherBankAccount, TeacherPayrollConfig, TeacherPayout
from system.models.membership import MembershipInvoice
from system.services.asaas_payroll import compute_available_balance
from system.models.calendar import ClassSession, SpecialClass as SpecialClassModel
from system.services.class_calendar import (
    _get_instructor_class_group_ids,
    get_instructor_checkin_history,
    get_student_checkin_history,
    get_today_classes_for_administrative,
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
from system.services.payroll_rules import calculate_monthly_payroll
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
        context["show_instructor_area"] = is_admin or is_administrative or is_instructor
        if person is None:
            context.update(_empty_context())
            return context

        if is_admin or is_instructor:
            context["today_classes"] = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        elif is_administrative:
            context["today_classes"] = get_today_classes_for_administrative(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        else:
            context["today_classes"] = get_today_classes_for_person(person)
            context["attendance_history"] = get_student_checkin_history(person)

        gp = compute_graduation_progress(person)
        context["graduation_progress"] = gp
        context["graduation_history"] = get_graduation_history(person)

        if gp and gp.current_belt_rank:
            belt = gp.current_belt_rank
            grade = gp.current_grade_number or 0
            slots = belt.get_grade_slots(grade)
            n = len(slots)
            tip_start, tip_width, stripe_w, stripe_gap = 232, 88, 12, 5
            if n > 0:
                total_w = n * stripe_w + (n - 1) * stripe_gap
                sx = tip_start + (tip_width - total_w) // 2
                stripes = [{"filled": f, "x": sx + i * (stripe_w + stripe_gap)} for i, f in enumerate(slots)]
            else:
                stripes = []
            context["belt_rank"] = belt
            context["belt_grade_number"] = grade
            context["belt_stripes"] = stripes
        else:
            context["belt_rank"] = None
            context["belt_grade_number"] = 0
            context["belt_stripes"] = []

        if is_instructor:
            context.update(_build_instructor_payroll_context(person))
            group_ids = _get_instructor_class_group_ids(person)
            regular_dates = set(
                ClassSession.objects.filter(
                    schedule__class_group_id__in=group_ids,
                    instructor_present=True,
                ).values_list("date", flat=True)
            )
            special_dates = set(
                SpecialClassModel.objects.filter(
                    teacher=person, instructor_present=True,
                ).values_list("date", flat=True)
            )
            context["instructor_attendance_count"] = len(regular_dates | special_dates)

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


def _build_instructor_payroll_context(person):
    calculation = calculate_monthly_payroll(person)
    available, base, committed = compute_available_balance(person)
    recent_payouts = list(
        TeacherPayout.objects.filter(person=person)
        .order_by("-reference_month", "-created_at")[:10]
    )
    try:
        payroll_config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        payroll_config = None
    try:
        payroll_bank = person.teacher_bank_account
    except TeacherBankAccount.DoesNotExist:
        payroll_bank = None
    return {
        "payroll_calculation": calculation,
        "payroll_available_balance": available,
        "payroll_base_salary": base,
        "payroll_committed_total": committed,
        "payroll_recent_payouts": recent_payouts,
        "payroll_config": payroll_config,
        "payroll_bank": payroll_bank,
    }


def _empty_context():
    return {
        "today_classes": [],
        "attendance_history": [],
        "graduation_progress": None,
        "graduation_history": [],
        "belt_rank": None,
        "belt_grade_number": 0,
        "belt_stripes": [],
        "active_trial_access": None,
        "billing_tabs": [],
        "payroll_calculation": None,
        "payroll_available_balance": None,
        "payroll_base_salary": None,
        "payroll_committed_total": None,
        "payroll_recent_payouts": [],
        "payroll_config": None,
        "payroll_bank": None,
        "instructor_attendance_count": 0,
    }
