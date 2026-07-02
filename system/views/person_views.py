from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Prefetch
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms import PersonForm, PersonListFilterForm, PersonTypeForm
from system.models import (
    AuditAction,
    AuditModule,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Graduation,
    IbjjfAgeCategory,
    Person,
    PersonType,
)
from system.models.membership import Membership, MembershipInvoice
from system.models.plan import SubscriptionPlan
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.selectors import (
    compute_veteran_member_since,
    get_person_queryset,
    is_veteran_plan_eligible,
)
from system.services.access_requests import get_administrative_access_requests_for_person
from system.services.audit import record_audit_event, resolve_actor_label
from system.services.class_catalog import prepare_class_group_for_display
from system.services.class_overview import build_class_group_filter_value
from system.services.class_requests import get_class_catalog_requests_history_for_person
from system.services.graduation import compute_graduation_progress, get_graduation_history
from system.services.membership import get_active_membership, get_membership_owner
from system.services.veteran_plan import approve_veteran_plan, revoke_veteran_plan
from system.constants import (
    ADMINISTRATIVE_PERSON_TYPE_CODES,
    CLASS_ENROLLMENT_PERSON_TYPE_CODES,
    INSTRUCTOR_PERSON_TYPE_CODES,
    PEOPLE_SUPPORT_PERSON_TYPE_CODES,
    PortalCapability,
)
from system.views.portal_mixins import PortalRoleRequiredMixin


class AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES
    required_capabilities = (PortalCapability.MANAGE_ACADEMY,)


class PeopleSupportRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = PEOPLE_SUPPORT_PERSON_TYPE_CODES
    required_capabilities = (PortalCapability.SUPPORT_PEOPLE,)


def _can_manage_people(request):
    return bool(
        PortalCapability.MANAGE_PEOPLE
        in getattr(request, "portal_capabilities", set())
        or getattr(request, "portal_is_technical_admin", False)
    )


class ModalCrudMixin:
    """Renderiza a variante modal (iframe) quando a rota recebe ?modal=1."""

    modal_template_name = None
    modal_name = ""

    def is_modal(self):
        return self.request.GET.get("modal") == "1"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.is_modal():
            response["X-Frame-Options"] = "SAMEORIGIN"
        return response

    def get_template_names(self):
        if self.is_modal() and self.modal_template_name:
            return [self.modal_template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_modal():
            context["is_modal"] = True
            context["crud_modal_name"] = self.modal_name
        return context


class ModalFormMixin(ModalCrudMixin):
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.is_modal():
            return render(
                self.request,
                "lv/modal_done.html",
                {"crud_modal_name": self.modal_name},
            )
        return response


class PersonListView(PeopleSupportRequiredMixin, ListView):
    model = Person
    template_name = "people/person_list.html"
    context_object_name = "people"

    def dispatch(self, request, *args, **kwargs):
        self.filter_form = PersonListFilterForm(request.GET or None)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.filter_form.is_valid():
            queryset = get_person_queryset(filters=self.filter_form.cleaned_data)
        else:
            queryset = get_person_queryset()
        if not _can_manage_people(self.request):
            queryset = queryset.filter(
                person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["can_manage_people"] = _can_manage_people(self.request)
        context["person_create_label"] = (
            "Nova pessoa" if context["can_manage_people"] else "Cadastrar aluno"
        )
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        people = list(context["people"])
        context["people"] = people
        for person in people:
            _hydrate_person_relationships(person, active_ibjjf_categories)
        return context


class PersonCreateView(ModalFormMixin, PeopleSupportRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    modal_template_name = "people/person_form_modal.html"
    modal_name = "person-create"
    success_url = reverse_lazy("system:person-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not _can_manage_people(self.request):
            kwargs["person_type_codes"] = CLASS_ENROLLMENT_PERSON_TYPE_CODES
            kwargs["show_payroll_fields"] = False
            kwargs["show_operational_role_fields"] = False
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        record_audit_event(
            module=AuditModule.PERSON,
            action=AuditAction.CREATE,
            actor_label=resolve_actor_label(self.request),
            entity_label=self.object.full_name,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_people"] = _can_manage_people(self.request)
        return context


class PersonUpdateView(ModalFormMixin, PeopleSupportRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    modal_template_name = "people/person_form_modal.html"
    modal_name = "person-edit"
    success_url = reverse_lazy("system:person-list")

    def get_queryset(self):
        queryset = get_person_queryset()
        if not _can_manage_people(self.request):
            queryset = queryset.filter(
                person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES
            )
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not _can_manage_people(self.request):
            kwargs["person_type_codes"] = CLASS_ENROLLMENT_PERSON_TYPE_CODES
            kwargs["show_payroll_fields"] = False
            kwargs["show_operational_role_fields"] = False
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        record_audit_event(
            module=AuditModule.PERSON,
            action=AuditAction.UPDATE,
            actor_label=resolve_actor_label(self.request),
            entity_label=self.object.full_name,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_people"] = _can_manage_people(self.request)
        person = context["object"]
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        _hydrate_person_relationships(person, active_ibjjf_categories)
        context["graduation_progress"] = compute_graduation_progress(person)
        context["graduation_history"] = get_graduation_history(person)
        context["has_official_graduation"] = Graduation.objects.filter(
            person=person
        ).exists()
        return context


class PersonDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Person
    template_name = "people/person_confirm_delete.html"
    success_url = reverse_lazy("system:person-list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError as error:
            blockers = _format_person_delete_blockers(error.protected_objects)
            messages.error(
                self.request,
                (
                    f"Não foi possível excluir {self.object.full_name} porque há "
                    f"vínculo protegido em {blockers}. Remova ou substitua esse "
                    "vínculo antes de excluir."
                ),
            )
            return redirect("system:person-detail", pk=self.object.pk)
        record_audit_event(
            module=AuditModule.PERSON,
            action=AuditAction.DELETE,
            actor_label=resolve_actor_label(self.request),
            entity_label=self.object.full_name,
        )
        messages.success(
            self.request,
            f"{self.object.full_name} foi excluído(a) com sucesso.",
        )
        return HttpResponseRedirect(success_url)


class PersonDetailView(ModalCrudMixin, PeopleSupportRequiredMixin, DetailView):
    model = Person
    template_name = "people/person_detail.html"
    modal_template_name = "people/person_detail_modal.html"
    modal_name = "person-view"
    context_object_name = "person"

    def get_queryset(self):
        queryset = get_person_queryset()
        if not _can_manage_people(self.request):
            queryset = queryset.filter(
                person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_people"] = _can_manage_people(self.request)
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        _hydrate_person_relationships(context["person"], active_ibjjf_categories)
        context["graduation_progress"] = compute_graduation_progress(context["person"])
        context["graduation_history"] = get_graduation_history(context["person"])
        context["belt_stripes_detail"] = _compute_belt_stripes(context["graduation_progress"])
        if not context["can_manage_people"]:
            return context
        person = context["person"]
        context["access_request_history"] = get_administrative_access_requests_for_person(
            person, limit=20
        )
        context["class_request_history"] = get_class_catalog_requests_history_for_person(
            person, limit=20
        )
        billing_person = get_membership_owner(person)
        memberships = list(
            Membership.objects.filter(person=billing_person)
            .select_related("plan")
            .order_by("-created_at")
        )
        context["memberships"] = memberships
        active_membership = get_active_membership(person)
        context["active_membership"] = active_membership
        context["billing_owner"] = billing_person
        if active_membership is not None:
            context["person_invoices"] = list(
                MembershipInvoice.objects.filter(membership=active_membership)
                .order_by("-paid_at", "-created_at")[:10]
            )
        else:
            context["person_invoices"] = []
        context["person_orders"] = list(
            RegistrationOrder.objects.filter(person=billing_person)
            .select_related("plan")
            .order_by("-created_at")[:15]
        )
        context["pending_orders"] = [
            o for o in context["person_orders"]
            if o.payment_status not in (
                PaymentStatus.PAID,
                PaymentStatus.EXEMPTED,
                PaymentStatus.REFUNDED,
            )
        ]
        context["available_plans"] = list(
            SubscriptionPlan.objects.filter(is_active=True).order_by("display_name")
        )
        context["veteran_plan_owner"] = billing_person
        context["veteran_member_since"] = compute_veteran_member_since(billing_person)
        context["veteran_plan_eligible"] = is_veteran_plan_eligible(billing_person)
        context["veteran_plan_tenure_years"] = settings.VETERAN_PLAN_TENURE_YEARS
        return context


class VeteranPlanDecisionView(PortalRoleRequiredMixin, View):
    required_capabilities = (PortalCapability.MANAGE_PEOPLE, PortalCapability.MANAGE_ACADEMY)

    def post(self, request, pk, *args, **kwargs):
        person = get_object_or_404(Person, pk=pk)
        action = request.POST.get("action")
        notes = request.POST.get("notes", "")
        actor = getattr(request, "portal_person", None)
        if action == "revoke":
            revoke_veteran_plan(person, revoked_by=actor, notes=notes)
            messages.success(request, "Plano Veterano revogado.")
        else:
            approve_veteran_plan(person, approved_by=actor, notes=notes)
            messages.success(request, "Plano Veterano aprovado.")
        return redirect("system:person-detail", pk=person.pk)


class PersonTypeListView(AdministrativeRequiredMixin, ListView):
    model = PersonType
    template_name = "person_types/person_type_list.html"
    context_object_name = "person_types"

    def get_queryset(self):
        return PersonType.objects.annotate(people_count=Count("people")).order_by(
            "display_name"
        )


class PersonTypeCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    modal_name = "person-type-create"
    success_url = reverse_lazy("system:person-type-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Novo perfil"
        return context


class PersonTypeUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    modal_name = "person-type-edit"
    success_url = reverse_lazy("system:person-type-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar perfil"
        return context


class PersonTypeDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = PersonType
    template_name = "person_types/person_type_confirm_delete.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeDetailView(AdministrativeRequiredMixin, DetailView):
    model = PersonType
    template_name = "person_types/person_type_detail.html"
    context_object_name = "person_type"

    def get_queryset(self):
        return PersonType.objects.prefetch_related(
            Prefetch(
                "people",
                queryset=Person.objects.order_by("full_name"),
            )
        )


def _format_person_delete_blockers(protected_objects):
    labels = []
    label_by_model = {
        "ClassGroup": "turma principal",
        "SpecialClass": "aula especial",
        "TeacherPayout": "repasse financeiro",
    }
    for protected_object in protected_objects:
        label = label_by_model.get(
            protected_object.__class__.__name__,
            "vínculo protegido",
        )
        if label not in labels:
            labels.append(label)
    if not labels:
        return "vínculo protegido"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} e {labels[1]}"
    return f"{', '.join(labels[:-1])} e {labels[-1]}"


def _hydrate_person_relationships(person, active_ibjjf_categories):
    active_enrollments = list(person.class_enrollments.all())
    student_relationships = _build_student_relationships(active_enrollments)
    person_type_code = person.person_type.code if person.person_type_id else ""
    person.active_group_labels = student_relationships["group_labels"]
    person.active_schedule_labels = student_relationships["schedule_labels"]
    person.active_schedule_sections = student_relationships["schedule_sections"]
    person.teaching_groups = _get_person_teaching_groups(person)
    person.teaching_group_labels = [
        class_group.catalog_title for class_group in person.teaching_groups
    ]
    person.teaching_schedule_labels = []
    for class_group in person.teaching_groups:
        for label in class_group.schedule_labels:
            if label not in person.teaching_schedule_labels:
                person.teaching_schedule_labels.append(label)
    person.teaching_schedule_sections = _build_grouped_schedule_sections(
        person.teaching_groups
    )
    person.resolved_ibjjf_category = next(
        (
            category
            for category in active_ibjjf_categories
            if person.get_age() is not None and category.matches_age(person.get_age())
        ),
        None,
    )
    person.show_student_context = bool(
        person_type_code in CLASS_ENROLLMENT_PERSON_TYPE_CODES
        or person.active_group_labels
    )
    person.show_teacher_context = bool(
        person_type_code in INSTRUCTOR_PERSON_TYPE_CODES
        or person.teaching_group_labels
    )


def _get_person_teaching_groups(person):
    teaching_groups = []
    seen_group_ids = set()
    for class_group in person.primary_class_groups.all():
        prepared_group = prepare_class_group_for_display(class_group)
        if prepared_group.pk in seen_group_ids:
            continue
        teaching_groups.append(prepared_group)
        seen_group_ids.add(prepared_group.pk)
    for assignment in person.class_instructor_assignments.all():
        prepared_group = prepare_class_group_for_display(assignment.class_group)
        if prepared_group.pk in seen_group_ids:
            continue
        teaching_groups.append(prepared_group)
        seen_group_ids.add(prepared_group.pk)
    return teaching_groups


def _build_student_relationships(active_enrollments):
    grouped_labels = OrderedDict()
    grouped_schedule_entries = OrderedDict()
    schedule_entries = OrderedDict()

    for enrollment in active_enrollments:
        class_group = enrollment.class_group
        group_key = build_class_group_filter_value(
            class_group.class_category_id,
            class_group.display_name,
        )
        if group_key not in grouped_labels:
            grouped_labels[group_key] = (
                f"{class_group.class_category.display_name} · {class_group.display_name}"
            )
        if group_key not in grouped_schedule_entries:
            grouped_schedule_entries[group_key] = OrderedDict()
        for schedule in class_group.schedules.all():
            schedule_key = (schedule.weekday, schedule.start_time.strftime("%H:%M"))
            schedule_label = (
                f"{schedule.get_weekday_display()} · {schedule.start_time.strftime('%H:%M')}"
            )
            weekday_label = schedule.get_weekday_display()
            time_label = schedule.start_time.strftime("%H:%M")
            if weekday_label not in grouped_schedule_entries[group_key]:
                grouped_schedule_entries[group_key][weekday_label] = []
            if time_label not in grouped_schedule_entries[group_key][weekday_label]:
                grouped_schedule_entries[group_key][weekday_label].append(time_label)
            if schedule_key in schedule_entries:
                continue
            schedule_entries[schedule_key] = schedule_label

    return {
        "group_labels": list(grouped_labels.values()),
        "schedule_labels": list(schedule_entries.values()),
        "schedule_sections": [
            {
                "group_label": grouped_labels[group_key],
                "schedule_labels": [
                    f"{weekday_label} · {time_label}"
                    for weekday_label, time_labels in grouped_schedule_entries[group_key].items()
                    for time_label in _sort_time_labels(time_labels)
                ],
                "schedule_count": sum(
                    len(time_labels)
                    for time_labels in grouped_schedule_entries[group_key].values()
                ),
                "weekday_sections": [
                    {
                        "weekday_label": weekday_label,
                        "time_labels": _sort_time_labels(time_labels),
                    }
                    for weekday_label, time_labels in grouped_schedule_entries[group_key].items()
                ],
            }
            for group_key in grouped_labels
        ],
    }


def _build_grouped_schedule_sections(class_groups):
    sections = []
    for class_group in class_groups:
        schedule_labels = []
        seen_labels = set()
        weekday_entries = OrderedDict()
        for label in class_group.schedule_labels:
            if label in seen_labels:
                continue
            schedule_labels.append(label)
            seen_labels.add(label)
        for schedule in class_group.schedule_cards:
            weekday_label = schedule.get_weekday_display()
            time_label = schedule.start_time.strftime("%H:%M")
            if weekday_label not in weekday_entries:
                weekday_entries[weekday_label] = []
            if time_label not in weekday_entries[weekday_label]:
                weekday_entries[weekday_label].append(time_label)
        sections.append(
            {
                "group_label": class_group.catalog_title,
                "schedule_labels": schedule_labels,
                "schedule_count": len(schedule_labels),
                "weekday_sections": [
                    {
                        "weekday_label": weekday_label,
                        "time_labels": _sort_time_labels(time_labels),
                    }
                    for weekday_label, time_labels in weekday_entries.items()
                ],
            }
        )
    return sections


def _sort_time_labels(time_labels):
    return sorted(
        time_labels,
        key=lambda value: tuple(int(part) for part in value.split(":", 1)),
    )


def _compute_belt_stripes(graduation_progress):
    if graduation_progress is None or graduation_progress.current_belt_rank is None:
        return []
    belt = graduation_progress.current_belt_rank
    grade = graduation_progress.current_grade_number or 0
    slots = belt.get_grade_slots(grade)
    n = len(slots)
    if n == 0:
        return []
    tip_start, tip_width, stripe_w, stripe_gap = 232, 88, 12, 5
    total_w = n * stripe_w + (n - 1) * stripe_gap
    sx = tip_start + (tip_width - total_w) // 2
    return [{"filled": f, "x": sx + i * (stripe_w + stripe_gap)} for i, f in enumerate(slots)]
