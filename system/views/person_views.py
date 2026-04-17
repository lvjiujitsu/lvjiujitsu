from collections import OrderedDict

from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.db.models import Count, Prefetch

from system.forms import PersonForm, PersonListFilterForm, PersonTypeForm
from system.models import (
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    IbjjfAgeCategory,
    Person,
    PersonType,
)
from system.models.membership import Membership, MembershipInvoice
from system.models.plan import SubscriptionPlan
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.selectors import get_person_queryset
from system.services.class_catalog import prepare_class_group_for_display
from system.services.class_overview import build_class_group_filter_value
from system.services.membership import get_active_membership, get_membership_owner
from system.views.portal_mixins import PortalRoleRequiredMixin


class AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ("administrative-assistant",)


class PersonListView(AdministrativeRequiredMixin, ListView):
    model = Person
    template_name = "people/person_list.html"
    context_object_name = "people"

    def dispatch(self, request, *args, **kwargs):
        self.filter_form = PersonListFilterForm(request.GET or None)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.filter_form.is_valid():
            return get_person_queryset(filters=self.filter_form.cleaned_data)
        return get_person_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        for person in context["people"]:
            _hydrate_person_relationships(person, active_ibjjf_categories)
        return context


class PersonCreateView(AdministrativeRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    success_url = reverse_lazy("system:person-list")


class PersonUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    success_url = reverse_lazy("system:person-list")


class PersonDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Person
    template_name = "people/person_confirm_delete.html"
    success_url = reverse_lazy("system:person-list")


class PersonDetailView(AdministrativeRequiredMixin, DetailView):
    model = Person
    template_name = "people/person_detail.html"
    context_object_name = "person"

    def get_queryset(self):
        return get_person_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        _hydrate_person_relationships(context["person"], active_ibjjf_categories)
        person = context["person"]
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
        return context


class PersonTypeListView(AdministrativeRequiredMixin, ListView):
    model = PersonType
    template_name = "person_types/person_type_list.html"
    context_object_name = "person_types"

    def get_queryset(self):
        return PersonType.objects.annotate(people_count=Count("people")).order_by(
            "display_name"
        )


class PersonTypeCreateView(AdministrativeRequiredMixin, CreateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    success_url = reverse_lazy("system:person-type-list")


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


def _hydrate_person_relationships(person, active_ibjjf_categories):
    active_enrollments = list(person.class_enrollments.all())
    student_relationships = _build_student_relationships(active_enrollments)
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
