from django.db.models import Count, Prefetch
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms import ClassCategoryForm
from system.models import (
    ClassCategory,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
)
from system.services.class_catalog import prepare_class_group_for_display
from system.views.person_views import AdministrativeRequiredMixin


class ClassCategoryListView(AdministrativeRequiredMixin, ListView):
    model = ClassCategory
    template_name = "class_categories/class_category_list.html"
    context_object_name = "class_categories"

    def get_queryset(self):
        return ClassCategory.objects.annotate(
            group_count=Count("class_groups", distinct=True),
            person_count=Count("people", distinct=True),
        ).order_by("display_order", "display_name")


class ClassCategoryCreateView(AdministrativeRequiredMixin, CreateView):
    model = ClassCategory
    form_class = ClassCategoryForm
    template_name = "class_categories/class_category_form.html"
    success_url = reverse_lazy("system:class-category-list")


class ClassCategoryUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = ClassCategory
    form_class = ClassCategoryForm
    template_name = "class_categories/class_category_form.html"
    success_url = reverse_lazy("system:class-category-list")


class ClassCategoryDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = ClassCategory
    template_name = "class_categories/class_category_confirm_delete.html"
    success_url = reverse_lazy("system:class-category-list")


class ClassCategoryDetailView(AdministrativeRequiredMixin, DetailView):
    model = ClassCategory
    template_name = "class_categories/class_category_detail.html"
    context_object_name = "class_category"

    def get_queryset(self):
        return ClassCategory.objects.prefetch_related(
            Prefetch(
                "class_groups",
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
                "people",
                queryset=Person.objects.select_related("person_type").order_by("full_name"),
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        linked_class_groups = [
            prepare_class_group_for_display(class_group)
            for class_group in context["class_category"].class_groups.all()
        ]
        linked_people_map = {
            person.pk: person for person in context["class_category"].people.all()
        }
        for class_group in linked_class_groups:
            if class_group.main_teacher_id:
                linked_people_map[class_group.main_teacher.pk] = class_group.main_teacher
            for assignment in class_group.instructor_assignments.all():
                linked_people_map[assignment.person.pk] = assignment.person
        context["linked_class_groups"] = linked_class_groups
        context["linked_people"] = list(linked_people_map.values())
        return context
