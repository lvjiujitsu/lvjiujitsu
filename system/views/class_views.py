from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from system.forms import ClassGroupForm, ClassScheduleForm
from system.forms.class_forms import get_class_group_schedule_formset
from system.models import ClassGroup, ClassSchedule
from system.services.class_catalog import (
    get_admin_class_group_queryset,
    get_admin_class_schedule_queryset,
    prepare_class_group_for_display,
)
from system.services.class_management import save_class_group_catalog
from system.views.person_views import AdministrativeRequiredMixin


class ClassGroupCatalogMixin:
    schedule_formset_class = None

    def get_schedule_formset(self):
        data = self.request.POST if self.request.method == "POST" else None
        return get_class_group_schedule_formset(
            data=data,
            instance=getattr(self, "object", None),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schedule_formset"] = kwargs.get("schedule_formset") or self.get_schedule_formset()
        return context

    def form_valid(self, form):
        schedule_formset = self.get_schedule_formset()
        schedule_formset.catalog_form = form
        if not schedule_formset.is_valid():
            return self.form_invalid(form, schedule_formset)
        self.object = save_class_group_catalog(
            form=form,
            schedule_formset=schedule_formset,
        )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, schedule_formset=None):
        target_formset = schedule_formset or self.get_schedule_formset()
        return self.render_to_response(
            self.get_context_data(
                form=form,
                schedule_formset=target_formset,
            )
        )


class ClassGroupListView(AdministrativeRequiredMixin, ListView):
    model = ClassGroup
    template_name = "classes/class_group_list.html"
    context_object_name = "class_groups"

    def get_queryset(self):
        return get_admin_class_group_queryset()


class ClassGroupCreateView(
    AdministrativeRequiredMixin,
    ClassGroupCatalogMixin,
    CreateView,
):
    model = ClassGroup
    form_class = ClassGroupForm
    template_name = "classes/class_group_form.html"
    success_url = reverse_lazy("system:class-group-list")


class ClassGroupUpdateView(
    AdministrativeRequiredMixin,
    ClassGroupCatalogMixin,
    UpdateView,
):
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

    def get_initial(self):
        initial = super().get_initial()
        class_group_id = self.request.GET.get("class_group")
        if class_group_id:
            initial["class_group"] = class_group_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_class_group"] = self._get_selected_class_group(
            context.get("form")
        )
        return context

    def _get_selected_class_group(self, form):
        if form is None:
            return None
        selected_id = (
            form["class_group"].value()
            or form.initial.get("class_group")
            or self.request.GET.get("class_group")
        )
        if not selected_id:
            return None
        class_group = form.fields["class_group"].queryset.filter(pk=selected_id).first()
        if class_group is None:
            return None
        return prepare_class_group_for_display(class_group)


class ClassScheduleUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = ClassSchedule
    form_class = ClassScheduleForm
    template_name = "class_schedules/class_schedule_form.html"
    success_url = reverse_lazy("system:class-schedule-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object and self.object.class_group_id:
            context["selected_class_group"] = prepare_class_group_for_display(
                self.object.class_group
            )
        return context


class ClassScheduleDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = ClassSchedule
    template_name = "class_schedules/class_schedule_confirm_delete.html"
    success_url = reverse_lazy("system:class-schedule-list")
