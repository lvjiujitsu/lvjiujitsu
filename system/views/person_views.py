from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.db.models import Prefetch

from system.forms import PersonForm, PersonTypeForm
from system.models import (
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    IbjjfAgeCategory,
    Person,
    PersonType,
)
from system.services.class_catalog import prepare_class_group_for_display
from system.views.portal_mixins import PortalRoleRequiredMixin


class AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ("administrative-assistant",)


class PersonListView(AdministrativeRequiredMixin, ListView):
    model = Person
    template_name = "people/person_list.html"
    context_object_name = "people"

    def get_queryset(self):
        return (
            Person.objects.select_related(
                "access_account",
                "person_type",
            )
            .prefetch_related(
                Prefetch(
                    "class_enrollments",
                    queryset=ClassEnrollment.objects.select_related(
                        "class_group",
                        "class_group__class_category",
                    ).filter(status="active"),
                ),
                Prefetch(
                    "primary_class_groups",
                    queryset=ClassGroup.objects.select_related(
                        "class_category",
                        "main_teacher",
                    ).prefetch_related(
                        Prefetch(
                            "schedules",
                            queryset=ClassSchedule.objects.filter(is_active=True).order_by(
                                "weekday",
                                "start_time",
                            ),
                        ),
                        Prefetch(
                            "instructor_assignments",
                            queryset=ClassInstructorAssignment.objects.select_related(
                                "person"
                            ).order_by("person__full_name"),
                        ),
                    ),
                ),
                Prefetch(
                    "class_instructor_assignments",
                    queryset=ClassInstructorAssignment.objects.select_related(
                        "class_group",
                        "class_group__class_category",
                        "class_group__main_teacher",
                    ).prefetch_related(
                        Prefetch(
                            "class_group__schedules",
                            queryset=ClassSchedule.objects.filter(is_active=True).order_by(
                                "weekday",
                                "start_time",
                            ),
                        ),
                        Prefetch(
                            "class_group__instructor_assignments",
                            queryset=ClassInstructorAssignment.objects.select_related(
                                "person"
                            ).order_by("person__full_name"),
                        ),
                    ),
                ),
            )
            .order_by("full_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        for person in context["people"]:
            active_enrollments = list(person.class_enrollments.all())
            person.active_group_labels = [
                f"{enrollment.class_group.class_category.display_name} · {enrollment.class_group.display_name}"
                for enrollment in active_enrollments
            ]
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
            person.teaching_group_labels = [
                class_group.catalog_title for class_group in teaching_groups
            ]
            person.teaching_schedule_labels = []
            for class_group in teaching_groups:
                for label in class_group.schedule_labels:
                    if label not in person.teaching_schedule_labels:
                        person.teaching_schedule_labels.append(label)
            person.resolved_ibjjf_category = next(
                (
                    category
                    for category in active_ibjjf_categories
                    if person.get_age() is not None and category.matches_age(person.get_age())
                ),
                None,
            )
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


class PersonTypeListView(AdministrativeRequiredMixin, ListView):
    model = PersonType
    template_name = "person_types/person_type_list.html"
    context_object_name = "person_types"


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
