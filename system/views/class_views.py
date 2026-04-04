from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from system.forms import ClassGroupForm, ClassScheduleForm
from system.models import ClassGroup, ClassSchedule
from system.services.class_catalog import (
    get_admin_class_group_queryset,
    get_admin_class_schedule_queryset,
)
from system.views.person_views import AdministrativeRequiredMixin


class ClassGroupListView(AdministrativeRequiredMixin, ListView):
    model = ClassGroup
    template_name = "classes/class_group_list.html"
    context_object_name = "class_groups"

    def get_queryset(self):
        return get_admin_class_group_queryset()


class ClassGroupCreateView(AdministrativeRequiredMixin, CreateView):
    model = ClassGroup
    form_class = ClassGroupForm
    template_name = "classes/class_group_form.html"
    success_url = reverse_lazy("system:class-group-list")


class ClassGroupUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = ClassGroup
    form_class = ClassGroupForm
    template_name = "classes/class_group_form.html"
    success_url = reverse_lazy("system:class-group-list")


class ClassGroupDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = ClassGroup
    template_name = "classes/class_group_confirm_delete.html"
    success_url = reverse_lazy("system:class-group-list")


class ClassScheduleListView(AdministrativeRequiredMixin, ListView):
    model = ClassSchedule
    template_name = "class_schedules/class_schedule_list.html"
    context_object_name = "class_schedules"

    def get_queryset(self):
        return get_admin_class_schedule_queryset()


class ClassScheduleCreateView(AdministrativeRequiredMixin, CreateView):
    model = ClassSchedule
    form_class = ClassScheduleForm
    template_name = "class_schedules/class_schedule_form.html"
    success_url = reverse_lazy("system:class-schedule-list")


class ClassScheduleUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = ClassSchedule
    form_class = ClassScheduleForm
    template_name = "class_schedules/class_schedule_form.html"
    success_url = reverse_lazy("system:class-schedule-list")


class ClassScheduleDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = ClassSchedule
    template_name = "class_schedules/class_schedule_confirm_delete.html"
    success_url = reverse_lazy("system:class-schedule-list")
