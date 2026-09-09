from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views import View
from django.views.generic import RedirectView, TemplateView

from system.core.audit import AuditAction
from system.business_rule.forms import ClientProfileForm
from system.business_rule.constants import AuditModule
from system.business_rule.models.calendar import ClassSession, SpecialClass as SpecialClassModel
from system.business_rule.selectors.home_context import (
    build_attendance_history_items,
    build_belt_context,
    build_billing_context,
    build_dependents,
    build_graduation_tabs,
    build_instructor_payroll_context,
    build_payment_history_items,
    build_profile_tabs,
    build_today_classes_tabs,
    can_access_people,
    can_manage_access_requests,
    can_manage_class_requests,
    client_profile_payload,
    empty_context,
    get_active_instructor_choices,
    get_portal_display_name,
    json_form_errors,
    merge_class_entries,
    role_labels,
)
from system.business_rule.services.class_calendar import (
    get_instructor_class_group_ids,
    get_instructor_checkin_history,
    get_student_checkin_history,
    get_today_classes_for_administrative,
    get_today_classes_for_instructor,
    get_today_classes_for_person,
    get_today_classes_staff_overview,
)
from system.business_rule.services.financial_dashboard import build_financial_dashboard
from system.business_rule.services.graduation import compute_graduation_progress, get_graduation_history
from system.business_rule.services.membership import has_dependents
from system.business_rule.services.membership_timeline import build_client_timeline
from system.business_rule.services.access_requests import (
    get_administrative_access_requests_for_person,
    get_pending_administrative_access_request_count,
)
from system.business_rule.services.class_requests import (
    get_class_catalog_requests_for_person,
    get_pending_class_catalog_request_count,
)
from system.business_rule.services.audit import record_event
from system.business_rule.access import (
    is_administrative,
    is_instructor,
    is_student,
    is_technical_admin,
    logout_portal_identity,
    portal_person,
    supports_classes,
)
from system.business_rule.access import PortalLoginRequiredMixin


class DashboardRedirectView(PortalLoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse("system:home")


class HomeView(PortalLoginRequiredMixin, TemplateView):
    template_name = "business_rule/home/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        person = portal_person(request)

        is_admin = is_technical_admin(request)
        administrative = is_administrative(request)
        instructor = is_instructor(request)
        student = is_student(request)
        can_support_classes = supports_classes(request)

        today = timezone.localdate()
        context["today_weekday"] = date_format(today, "l")
        context["today_date"] = date_format(today, "SHORT_DATE_FORMAT")
        context["today_iso"] = today.strftime("%Y-%m-%d")

        context["is_admin"] = is_admin
        context["is_administrative"] = administrative
        context["is_instructor"] = instructor
        context["is_student"] = student
        context["client_person"] = person
        context["can_support_classes"] = can_support_classes
        context["show_staff_area"] = is_admin or administrative
        context["show_instructor_area"] = (
            is_admin or administrative or instructor or can_support_classes
        )
        context["can_create_special_classes"] = context["show_instructor_area"]
        context["today_classes_toolbar"] = (
            "full" if context["show_instructor_area"] else "overview"
        )
        context["can_access_people"] = can_access_people(request)
        context["can_manage_class_requests"] = can_manage_class_requests(request)
        context["can_manage_access_requests"] = can_manage_access_requests(request)
        context["portal_display_name"] = get_portal_display_name(request)
        context["role_labels"] = role_labels(
            person,
            instructor,
            administrative,
            can_support_classes,
        )
        context["client_profile_update_url"] = reverse("system:client-profile-update")
        context["client_profile_deactivate_url"] = reverse("system:client-profile-deactivate")
        context["client_profile_form"] = (
            ClientProfileForm(instance=person) if person is not None else None
        )
        context.update(empty_context())

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
        trains = bool(instructor or student or person.jiu_jitsu_belt or enrolled)
        person_has_dependents = has_dependents(person)
        context["has_personal_area"] = trains
        context["show_dependents_area"] = bool(student or person_has_dependents)
        context["dependent_add_url"] = reverse("system:dependent-add")
        context["dependent_add_modal_url"] = (
            f"{context['dependent_add_url']}?modal=1"
        )
        context["dependent_modal_open"] = request.GET.get("dependent_modal") == "1"
        context["needs_split"] = bool(trains and context["show_staff_area"])
        context["show_billing_area"] = bool(trains or person_has_dependents)

        dependent_people = []
        family_memberships = None
        if person_has_dependents:
            context["dependents"], dependent_people, family_memberships = build_dependents(
                person
            )
        else:
            context["dependents"] = []

        if trains:
            context["my_classes"] = get_today_classes_for_person(person)
            context["graduation_progress"] = compute_graduation_progress(person)
            context["graduation_history"] = get_graduation_history(person)
            context.update(build_belt_context(context["graduation_progress"]))

        is_pure_student = False
        if instructor or (can_support_classes and not administrative):
            support_classes = get_today_classes_for_instructor(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
            if trains and not instructor:
                context["today_classes"] = merge_class_entries(
                    context["my_classes"], support_classes
                )
            else:
                context["today_classes"] = support_classes
        elif is_admin or administrative:
            context["today_classes"] = get_today_classes_for_administrative(person)
            context["attendance_history"] = get_instructor_checkin_history(person)
        elif trains:
            context["today_classes"] = context["my_classes"]
            context["attendance_history"] = get_student_checkin_history(person)
            is_pure_student = True

        context["graduation_tabs"] = build_graduation_tabs(context)
        context["today_classes_tabs"] = (
            build_today_classes_tabs(context) if is_pure_student else []
        )
        context["attendance_history_items"] = build_attendance_history_items(context)

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
            context["instructor_choices"] = get_active_instructor_choices()

        if instructor:
            context.update(build_instructor_payroll_context(person))
            group_ids = get_instructor_class_group_ids(person)
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
            context.update(
                build_billing_context(
                    person,
                    memberships_by_person=family_memberships,
                    dependent_people=dependent_people,
                )
            )
            context["payment_history_items"] = build_payment_history_items(
                context.get("billing_tabs")
            )
            context["membership_timeline_events"] = build_client_timeline(person)

        context["profile_tabs"] = build_profile_tabs(context)

        return context


class ClientProfileUpdateView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        person = portal_person(request)
        if person is None:
            return JsonResponse({"success": False, "error": "Não autenticado."}, status=403)

        form = ClientProfileForm(request.POST, instance=person)
        if not form.is_valid():
            return JsonResponse(
                {"success": False, "errors": json_form_errors(form)},
                status=400,
            )

        updated_person = form.save()
        record_event(
            updated_person.full_name,
            AuditAction.UPDATED,
            AuditModule.PERSON,
            updated_person.full_name,
            "Cadastro atualizado pelo próprio cliente.",
        )
        return JsonResponse({
            "success": True,
            "message": "Cadastro atualizado.",
            "person": client_profile_payload(updated_person),
        })


class ClientProfileDeactivateView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        person = portal_person(request)
        if person is None:
            return JsonResponse({"success": False, "error": "Não autenticado."}, status=403)
        if request.POST.get("confirm") != "ENCERRAR":
            return JsonResponse(
                {
                    "success": False,
                    "error": "Digite ENCERRAR para confirmar a exclusão do cadastro.",
                },
                status=400,
            )

        person_name = person.full_name
        with transaction.atomic():
            person.is_active = False
            person.save(update_fields=("is_active", "updated_at"))
            account = getattr(person, "access_account", None)
            if account is not None:
                account.is_active = False
                account.save(update_fields=("is_active", "updated_at"))
            record_event(
                person_name,
                AuditAction.DELETED,
                AuditModule.PERSON,
                person_name,
                "Cadastro encerrado pelo próprio cliente.",
            )

        logout_portal_identity(request)
        return JsonResponse({
            "success": True,
            "message": "Cadastro encerrado.",
            "redirect_url": reverse("system:login"),
        })
