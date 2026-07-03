from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import RedirectView, TemplateView

from system.constants import (
    PersonTypeCode,
    PortalCapability,
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
from system.services.plan_change import (
    build_membership_summary,
    build_plan_catalog,
    build_plan_catalog_filters,
    get_plan_change_lock,
)
from system.services.payroll_rules import calculate_monthly_payroll
from system.services.access_requests import (
    get_administrative_access_requests_for_person,
    get_pending_administrative_access_request_count,
)
from system.services.class_requests import (
    get_class_catalog_requests_for_person,
    get_pending_class_catalog_request_count,
)
from system.services.trial_access import get_active_trial_for_person
from system.services.portal_capabilities import get_operational_role_labels
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
        can_support_classes = getattr(request, "portal_supports_classes", False)

        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        context["today_iso"] = today.strftime("%Y-%m-%d")

        context["is_admin"] = is_admin
        context["is_administrative"] = is_administrative
        context["is_instructor"] = is_instructor
        context["is_student"] = is_student
        context["client_person"] = person
        context["can_support_classes"] = can_support_classes
        context["show_staff_area"] = is_admin or is_administrative
        context["show_instructor_area"] = (
            is_admin or is_administrative or is_instructor or can_support_classes
        )
        context["can_create_special_classes"] = context["show_instructor_area"]
        context["today_classes_toolbar"] = (
            "full" if context["show_instructor_area"] else "overview"
        )
        context["can_access_people"] = _can_access_people(request)
        context["can_manage_class_requests"] = _can_manage_class_requests(request)
        context["can_manage_access_requests"] = _can_manage_access_requests(request)
        context["portal_display_name"] = _get_portal_display_name(request)
        context["role_labels"] = _role_labels(
            person,
            is_instructor,
            is_administrative,
            can_support_classes,
        )
        context.update(_empty_context())

        if context["show_staff_area"]:
            context["financial_dashboard"] = build_financial_dashboard()
            context["pending_administrative_access_request_count"] = (
                get_pending_administrative_access_request_count()
            )
            context["pending_class_catalog_request_count"] = (
                get_pending_class_catalog_request_count()
            )

        if person is None:
            if context["show_staff_area"]:
                context["staff_today_classes"] = get_today_classes_staff_overview()
            return context

        context["administrative_access_requests"] = (
            get_administrative_access_requests_for_person(person)
        )
        context["class_catalog_requests"] = get_class_catalog_requests_for_person(person)

        enrolled = person.class_enrollments.filter(status="active").exists()
        trains = bool(is_instructor or is_student or person.jiu_jitsu_belt or enrolled)
        person_has_dependents = has_dependents(person)
        context["has_personal_area"] = trains
        context["show_dependents_area"] = bool(is_student or person_has_dependents)
        context["dependent_add_url"] = reverse("system:dependent-add")
        context["dependent_add_modal_url"] = (
            f"{context['dependent_add_url']}?modal=1"
        )
        context["dependent_modal_open"] = request.GET.get("dependent_modal") == "1"
        context["needs_split"] = bool(trains and context["show_staff_area"])
        context["show_billing_area"] = bool(trains or person_has_dependents)

        if trains:
            context["my_classes"] = get_today_classes_for_person(person)
            context["graduation_progress"] = compute_graduation_progress(person)
            context["graduation_history"] = get_graduation_history(person)
            context.update(_build_belt_context(context["graduation_progress"]))

        if is_instructor or (can_support_classes and not is_administrative):
            support_classes = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
            if trains and not is_instructor:
                context["today_classes"] = _merge_class_entries(
                    context["my_classes"], support_classes
                )
            else:
                context["today_classes"] = support_classes
        elif is_admin or is_administrative:
            context["today_classes"] = get_today_classes_for_administrative(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        elif trains:
            context["today_classes"] = context["my_classes"]
            context["attendance_history"] = get_student_checkin_history(person)

        if context["show_staff_area"] and not trains:
            context["staff_today_classes"] = get_today_classes_staff_overview()

        if context["needs_split"]:
            context["personal_today_classes"] = context["my_classes"]
            work_entries = [
                entry
                for entry in (context.get("today_classes") or [])
                if getattr(entry, "entry_role", None) != "student"
            ]
            if work_entries:
                context["staff_work_today_classes"] = work_entries
            elif not trains and context.get("staff_today_classes"):
                context["staff_work_today_classes"] = context["staff_today_classes"]

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

        if context["show_billing_area"]:
            context.update(_build_billing_context(person))

        if person_has_dependents:
            context["dependents"] = _build_dependents(person)

        return context


def _merge_class_entries(personal_entries, support_entries):
    seen_keys = set()
    merged = []
    for entry in list(personal_entries or []) + list(support_entries or []):
        key = (
            getattr(entry, "entry_role", None),
            getattr(entry, "schedule", None) and entry.schedule.pk,
            getattr(entry, "special_id", None),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(entry)
    merged.sort(key=lambda entry: entry.start_time or "")
    return merged


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


def _build_billing_context(person):
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

    own_membership = get_active_membership(person)
    plan_change_lock = get_plan_change_lock(own_membership)
    plan_change_locked = plan_change_lock["is_locked"]
    plan_change_catalog = (
        build_plan_catalog(person, own_membership)
        if own_membership and not plan_change_locked
        else []
    )
    plan_change_filters = build_plan_catalog_filters(plan_change_catalog)
    return {
        "active_trial_access": active_trial_access,
        "billing_tabs": billing_tabs,
        "client_billing_tab": billing_tabs[0] if billing_tabs else None,
        "plan_change_membership": own_membership,
        "plan_change_summary": build_membership_summary(own_membership),
        "plan_change_catalog": plan_change_catalog,
        "plan_change_filters": plan_change_filters,
        "plan_change_locked": plan_change_locked,
        "plan_change_available_on": plan_change_lock["available_on"],
        "plan_change_lock_message": plan_change_lock["message"],
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
            "graduation_progress": progress,
            "graduation_history": get_graduation_history(dependent),
            "today_classes": get_today_classes_for_person(dependent),
            "attendance_history": get_student_checkin_history(dependent, limit=5),
            "active_membership": get_active_membership(dependent),
            "billing_owner": get_membership_owner(dependent),
            "edit_url": reverse("system:dependent-edit", args=[dependent.pk]),
            "remove_url": reverse("system:dependent-remove", args=[dependent.pk]),
        })
    return dependents




def _role_labels(person, is_instructor, is_administrative, can_support_classes):
    labels = []
    if is_administrative:
        labels.append("Administrativo")
    if is_instructor:
        labels.append("Professor")
    if can_support_classes and not is_instructor and not is_administrative:
        labels.extend(get_operational_role_labels(person))
    trains_as_student = False
    if person is not None:
        trains_as_student = bool(
            person.jiu_jitsu_belt
            or person.class_enrollments.filter(status="active").exists()
            or (
                person.person_type_id
                and person.person_type.code in STUDENT_PORTAL_PERSON_TYPE_CODES
            )
        )
    if trains_as_student and "Aluno" not in labels:
        labels.append("Aluno")
    if person is not None and person.person_type_id:
        code = person.person_type.code
        if code == "guardian" and "Responsável" not in labels:
            labels.append("Responsável")
    return labels


def _empty_context():
    return {
        "has_personal_area": False,
        "needs_split": False,
        "my_classes": [],
        "personal_today_classes": [],
        "staff_today_classes": [],
        "staff_work_today_classes": [],
        "today_classes": [],
        "attendance_history": [],
        "graduation_progress": None,
        "graduation_history": [],
        "belt_rank": None,
        "belt_grade_number": 0,
        "belt_stripes": [],
        "active_trial_access": None,
        "billing_tabs": [],
        "client_billing_tab": None,
        "plan_change_membership": None,
        "plan_change_summary": None,
        "plan_change_catalog": [],
        "plan_change_filters": {"frequencies": [], "cycles": [], "methods": []},
        "plan_change_locked": False,
        "plan_change_available_on": None,
        "plan_change_lock_message": "",
        "dependents": [],
        "show_dependents_area": False,
        "show_billing_area": False,
        "dependent_add_url": "",
        "dependent_add_modal_url": "",
        "dependent_modal_open": False,
        "financial_dashboard": None,
        "pending_administrative_access_request_count": 0,
        "pending_class_catalog_request_count": 0,
        "administrative_access_requests": [],
        "class_catalog_requests": [],
        "payroll_calculation": None,
        "payroll_available_balance": None,
        "payroll_base_salary": None,
        "payroll_committed_total": None,
        "payroll_recent_payouts": [],
        "payroll_config": None,
        "payroll_bank": None,
        "instructor_attendance_count": 0,
        "instructor_choices": [],
        "today_classes_toolbar": "overview",
        "can_create_special_classes": False,
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
    return (
        PortalCapability.SUPPORT_PEOPLE
        in getattr(request, "portal_capabilities", set())
    )


def _can_manage_access_requests(request):
    if getattr(request, "portal_is_technical_admin", False):
        return True
    capabilities = getattr(request, "portal_capabilities", set())
    return bool(
        {
            PortalCapability.MANAGE_PEOPLE,
            PortalCapability.MANAGE_ACADEMY,
        }
        & set(capabilities)
    )


def _can_manage_class_requests(request):
    if getattr(request, "portal_is_technical_admin", False):
        return True
    capabilities = getattr(request, "portal_capabilities", set())
    return bool(
        {
            PortalCapability.MANAGE_CLASSES,
            PortalCapability.MANAGE_ACADEMY,
        }
        & set(capabilities)
    )


def _get_active_instructor_choices():
    return list(
        Person.objects.filter(
            person_type__code=PersonTypeCode.INSTRUCTOR,
            is_active=True,
        )
        .order_by("full_name")
        .values("pk", "full_name")
    )
