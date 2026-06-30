from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import RedirectView, TemplateView

from system.constants import (
    PEOPLE_SUPPORT_PERSON_TYPE_CODES,
    PersonTypeCode,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
)
from system.models import Person
from system.models.asaas import TeacherBankAccount, TeacherPayrollConfig, TeacherPayout
from system.models.calendar import ClassSession, SpecialClass as SpecialClassModel
from system.models.membership import MembershipInvoice
from system.services.asaas_payroll import compute_available_balance
from system.services.class_calendar import (
    _get_instructor_class_group_ids,
    get_instructor_checkin_history,
    get_student_checkin_history,
    get_today_classes_for_administrative,
    get_today_classes_for_instructor,
    get_today_classes_for_person,
    get_today_classes_staff_overview,
)
from system.services.financial_dashboard import build_financial_dashboard
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
        context["can_access_people"] = _can_access_people(request)
        context["portal_display_name"] = _get_portal_display_name(request)
        context["role_labels"] = _role_labels(person, is_instructor, is_administrative)
        context.update(_empty_context())

        if context["show_staff_area"]:
            context["financial_dashboard"] = build_financial_dashboard()

        if person is None:
            if context["show_staff_area"]:
                context["staff_today_classes"] = get_today_classes_staff_overview()
            return context

        enrolled = person.class_enrollments.filter(status="active").exists()
        trains = bool(is_instructor or is_student or person.jiu_jitsu_belt or enrolled)
        context["has_personal_area"] = trains
        context["needs_split"] = bool(
            trains and (has_dependents(person) or context["show_staff_area"])
        )

        if trains:
            context["my_classes"] = get_today_classes_for_person(person)
            context["graduation_progress"] = compute_graduation_progress(person)
            context["graduation_history"] = get_graduation_history(person)
            context.update(_build_belt_context(context["graduation_progress"]))

        if is_admin or is_instructor:
            context["today_classes"] = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        elif is_administrative:
            context["today_classes"] = get_today_classes_for_administrative(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        elif trains:
            context["today_classes"] = context["my_classes"]
            context["attendance_history"] = get_student_checkin_history(person)

        if context["show_staff_area"] and not trains:
            context["staff_today_classes"] = get_today_classes_staff_overview()

        if context["show_instructor_area"]:
            context["instructor_choices"] = _get_active_instructor_choices()

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
                    teacher=person,
                    instructor_present=True,
                ).values_list("date", flat=True)
            )
            context["instructor_attendance_count"] = len(regular_dates | special_dates)

        if is_student or has_dependents(person):
            context.update(_build_billing_context(person, is_student))

        if has_dependents(person):
            context["dependents"] = _build_dependents(person)

        return context


def _build_belt_context(graduation_progress):
    if graduation_progress and graduation_progress.current_belt_rank:
        belt = graduation_progress.current_belt_rank
        grade = graduation_progress.current_grade_number or 0
        slots = belt.get_grade_slots(grade)
        slot_count = len(slots)
        tip_start, tip_width, stripe_w, stripe_gap = 232, 88, 12, 5
        if slot_count > 0:
            total_w = slot_count * stripe_w + (slot_count - 1) * stripe_gap
            sx = tip_start + (tip_width - total_w) // 2
            stripes = [
                {"filled": filled, "x": sx + index * (stripe_w + stripe_gap)}
                for index, filled in enumerate(slots)
            ]
        else:
            stripes = []
        return {
            "belt_rank": belt,
            "belt_grade_number": grade,
            "belt_stripes": stripes,
        }
    return {
        "belt_rank": None,
        "belt_grade_number": 0,
        "belt_stripes": [],
    }


def _build_billing_context(person, is_student):
    if not is_student:
        return {
            "active_trial_access": None,
            "billing_tabs": [],
        }

    active_trial_access = get_active_trial_for_person(person)
    if has_dependents(person):
        billing_tabs = get_guardian_billing_tabs(person)
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
        billing_tabs = [{
            "person": person,
            "active_membership": active_membership,
            "pending_order": pending_order,
            "recent_invoices": recent_invoices,
            "is_active_tab": True,
            "billing_owner": billing_owner,
        }]
    return {
        "active_trial_access": active_trial_access,
        "billing_tabs": billing_tabs,
    }


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


def _build_dependents(guardian):
    from system.models.person import PersonRelationship, PersonRelationshipKind

    dependents = []
    relationships = (
        PersonRelationship.objects.filter(
            source_person=guardian,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        .select_related("target_person", "target_person__person_type")
        .order_by("target_person__full_name")
    )
    for relationship in relationships:
        dependent = relationship.target_person
        progress = compute_graduation_progress(dependent)
        dependents.append({
            "person": dependent,
            "belt_view": _build_belt_view(dependent, progress),
            "classes": get_today_classes_for_person(dependent),
            "billing": _billing_summary(dependent),
            "graduation_progress": progress,
        })
    return dependents


def _billing_summary(person):
    active = get_active_membership(person)
    return {
        "active_membership": active,
        "pending_order": get_latest_open_order(person),
        "plan_name": active.plan.display_name if active and active.plan_id else None,
    }


_BELT_BODY = {
    "white": "#ececec",
    "blue": "#1c52a3",
    "purple": "#5b3a8c",
    "brown": "#6a4528",
    "black": "#2b2b31",
    "red_black": "#b3261e",
    "red_white": "#b3261e",
    "red": "#b3261e",
}


def _build_belt_view(person, graduation_progress):
    code = getattr(person, "jiu_jitsu_belt", "") or ""
    if not code:
        return None

    body = _BELT_BODY.get(code, "#ececec")
    if code == "black":
        tip = "#b3261e"
    elif code == "red_white":
        tip = "#ececec"
    else:
        tip = "#17171a"

    grade = None
    if graduation_progress is not None:
        grade = graduation_progress.current_grade_number
    if grade is None:
        grade = getattr(person, "jiu_jitsu_stripes", None)
    grade = max(0, min(int(grade or 0), 6))

    tip_x, tip_w, stripe_w, gap = 230, 80, 6, 7
    total = grade * stripe_w + (grade - 1) * gap if grade > 0 else 0
    start = tip_x + (tip_w - total) // 2
    stripes = [start + i * (stripe_w + gap) for i in range(grade)]

    label = person.get_jiu_jitsu_belt_display()
    if graduation_progress is not None and graduation_progress.current_belt_rank:
        label = str(graduation_progress.current_belt_rank)

    return {
        "body": body,
        "tip": tip,
        "stripes": stripes,
        "needs_border": code in ("white", "red_white"),
        "grade": grade,
        "label": label,
    }


def _role_labels(person, is_instructor, is_administrative):
    labels = []
    if is_administrative:
        labels.append("Administrativo")
    if is_instructor:
        labels.append("Professor")
    if person is not None and person.person_type_id:
        code = person.person_type.code
        if code in STUDENT_PORTAL_PERSON_TYPE_CODES and "Aluno" not in labels:
            labels.append("Aluno")
        if code == "guardian":
            labels.append("Responsável")
    return labels


def _empty_context():
    return {
        "has_personal_area": False,
        "needs_split": False,
        "my_classes": [],
        "staff_today_classes": [],
        "today_classes": [],
        "attendance_history": [],
        "graduation_progress": None,
        "graduation_history": [],
        "belt_rank": None,
        "belt_grade_number": 0,
        "belt_stripes": [],
        "active_trial_access": None,
        "billing_tabs": [],
        "dependents": [],
        "financial_dashboard": None,
        "payroll_calculation": None,
        "payroll_available_balance": None,
        "payroll_base_salary": None,
        "payroll_committed_total": None,
        "payroll_recent_payouts": [],
        "payroll_config": None,
        "payroll_bank": None,
        "instructor_attendance_count": 0,
        "instructor_choices": [],
    }


def _get_portal_display_name(request):
    person = getattr(request, "portal_person", None)
    if person is not None:
        first_name = person.full_name.split()[0] if person.full_name else person.full_name
        return first_name or person.full_name
    user = getattr(request, "technical_admin_user", None)
    if user is not None:
        return user.get_short_name() or user.get_full_name() or user.get_username()
    return "LV"


def _can_access_people(request):
    if getattr(request, "portal_is_technical_admin", False):
        return True
    person = getattr(request, "portal_person", None)
    if person is None or not person.person_type_id:
        return False
    return person.person_type.code in PEOPLE_SUPPORT_PERSON_TYPE_CODES


def _get_active_instructor_choices():
    return list(
        Person.objects.filter(
            person_type__code=PersonTypeCode.INSTRUCTOR,
            is_active=True,
        )
        .order_by("full_name")
        .values("pk", "full_name")
    )
