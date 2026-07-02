from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms.plan_forms import PlanForm, PlanListFilterForm
from system.models.plan import SubscriptionPlan
from system.services.plan_management import (
    build_plan_kpis,
    build_plan_usage,
    get_plan_by_pk,
    get_plan_list,
)
from system.views.person_views import AdministrativeRequiredMixin, ModalFormMixin


class PlanListView(AdministrativeRequiredMixin, ListView):
    template_name = "plans/plan_list.html"
    context_object_name = "plans"

    def dispatch(self, request, *args, **kwargs):
        self.filter_form = PlanListFilterForm(request.GET or None)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.filter_form.is_valid():
            return get_plan_list(filters=self.filter_form.cleaned_data)
        return get_plan_list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plans = list(context["plans"])
        context["plans"] = plans
        context["filter_form"] = self.filter_form
        context["plan_kpis"] = build_plan_kpis(plans)
        return context


class PlanCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = SubscriptionPlan
    form_class = PlanForm
    template_name = "plans/plan_form.html"
    modal_template_name = "plans/plan_form_modal.html"
    modal_name = "plan-create"
    success_url = reverse_lazy("system:plan-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Plano criado com sucesso.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Novo plano"
        context["form_action_label"] = "Salvar plano"
        return context


class PlanDetailView(AdministrativeRequiredMixin, DetailView):
    template_name = "plans/plan_detail.html"
    context_object_name = "plan"

    def get_object(self, queryset=None):
        return get_plan_by_pk(self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = build_plan_usage(self.object)
        return context


class PlanUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = SubscriptionPlan
    form_class = PlanForm
    template_name = "plans/plan_form.html"
    modal_template_name = "plans/plan_form_modal.html"
    modal_name = "plan-edit"

    def get_success_url(self):
        return reverse_lazy("system:plan-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Plano atualizado com sucesso.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar plano"
        context["form_action_label"] = "Salvar plano"
        return context


class PlanDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = SubscriptionPlan
    template_name = "plans/plan_confirm_delete.html"
    success_url = reverse_lazy("system:plan-list")
    context_object_name = "plan"

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                "Este plano não pode ser excluído porque possui assinaturas vinculadas.",
            )
            return redirect("system:plan-detail", pk=self.object.pk)
        messages.success(self.request, "Plano excluído com sucesso.")
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = build_plan_usage(self.object)
        return context
