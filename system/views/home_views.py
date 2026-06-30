from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import RedirectView, TemplateView

from system.constants import (
    PEOPLE_SUPPORT_PERSON_TYPE_CODES,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
)
from system.models.asaas import TeacherPayout
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.services.asaas_payroll import compute_available_balance
from system.services.class_calendar import (
    get_today_classes_for_instructor,
    get_today_classes_for_person,
)
from system.services.graduation import compute_graduation_progress
from system.services.membership import (
    get_active_membership,
    get_latest_open_order,
    has_dependents,
)
from system.services.payroll_rules import calculate_monthly_payroll
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

        context["is_admin"] = is_admin
        context["is_administrative"] = is_administrative
        context["is_instructor"] = is_instructor
        context["is_student"] = is_student
        context["show_staff_area"] = is_admin or is_administrative
        context["can_access_people"] = _can_access_people(request)
        context["portal_display_name"] = _get_portal_display_name(request)
        context["role_labels"] = _role_labels(person, is_instructor, is_administrative)

        context["has_personal_area"] = False
        context["my_classes"] = []
        context["instructor_classes"] = []
        context["belt_view"] = None
        context["graduation_progress"] = None
        context["my_billing"] = None
        context["payroll"] = None
        context["dependents"] = []

        if person is None:
            context["needs_split"] = bool(context["show_staff_area"])
            return context

        enrolled = person.class_enrollments.filter(status="active").exists()
        trains = bool(is_instructor or is_student or person.jiu_jitsu_belt or enrolled)
        context["has_personal_area"] = trains

        if trains:
            context["my_classes"] = get_today_classes_for_person(person)
            context["graduation_progress"] = compute_graduation_progress(person)
            context["belt_view"] = _build_belt_view(person, context["graduation_progress"])
            context["my_billing"] = _billing_summary(person)

        if is_instructor:
            context["instructor_classes"] = get_today_classes_for_instructor(person)
            context["payroll"] = _payroll_summary(person)

        if has_dependents(person):
            context["dependents"] = _build_dependents(person)

        # "Minha área" só vira bloco separado quando há outra área (dependentes ou gestão).
        context["needs_split"] = bool(
            trains and (context["dependents"] or context["show_staff_area"])
        )

        return context


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


def _billing_summary(person):
    active = get_active_membership(person)
    return {
        "active_membership": active,
        "pending_order": get_latest_open_order(person),
        "plan_name": active.plan.display_name if active and active.plan_id else None,
    }


def _payroll_summary(person):
    available, _base, _committed = compute_available_balance(person)
    return {
        "available": available,
        "calculation": calculate_monthly_payroll(person),
        "recent_payouts": list(
            TeacherPayout.objects.filter(person=person)
            .order_by("-reference_month", "-created_at")[:5]
        ),
    }


def _build_dependents(guardian):
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
        })
    return dependents


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


def _get_portal_display_name(request):
    person = getattr(request, "portal_person", None)
    if person is not None:
        return person.full_name
    user = getattr(request, "technical_admin_user", None)
    if user is not None:
        return user.get_full_name() or user.get_username()
    return "LV"


def _can_access_people(request):
    if getattr(request, "portal_is_technical_admin", False):
        return True
    person = getattr(request, "portal_person", None)
    if person is None or not person.person_type_id:
        return False
    return person.person_type.code in PEOPLE_SUPPORT_PERSON_TYPE_CODES
