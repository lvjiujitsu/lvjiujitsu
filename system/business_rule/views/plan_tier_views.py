from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.business_rule.forms.plan_tier_forms import (
    PlanPriceForm,
    PlanTierForm,
    PlanTierListFilterForm,
)
from system.business_rule.models.plan import PlanPrice, PlanTier
from system.business_rule.services.plan_tier_management import (
    build_plan_price_usage,
    build_plan_tier_kpis,
    build_plan_tier_usage,
    get_plan_price_by_pk,
    get_plan_tier_by_pk,
    get_plan_tier_list,
)
from system.business_rule.views.person_views import ModalFormMixin
from system.business_rule.access import AdministrativeRequiredMixin


class PlanTierListView(AdministrativeRequiredMixin, ListView):
    template_name = "business_rule/plans/tier_list.html"
    context_object_name = "tiers"

    def dispatch(self, request, *args, **kwargs):
        self.filter_form = PlanTierListFilterForm(request.GET or None)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.filter_form.is_valid():
            return get_plan_tier_list(filters=self.filter_form.cleaned_data)
        return get_plan_tier_list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tiers = list(context["tiers"])
        context["tiers"] = tiers
        context["filter_form"] = self.filter_form
        context["tier_kpis"] = build_plan_tier_kpis(tiers)
        return context


class PlanTierCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = PlanTier
    form_class = PlanTierForm
    template_name = "business_rule/plans/tier_form.html"
    modal_template_name = "business_rule/plans/tier_form_modal.html"
    modal_name = "plan-tier-create"
    success_url = reverse_lazy("system:plan-tier-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Tier criado com sucesso.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Novo tier"
        context["form_action_label"] = "Salvar tier"
        return context


class PlanTierDetailView(AdministrativeRequiredMixin, DetailView):
    template_name = "business_rule/plans/tier_detail.html"
    context_object_name = "tier"

    def get_object(self, queryset=None):
        return get_plan_tier_by_pk(self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = build_plan_tier_usage(self.object)
        context["prices"] = self.object.prices.order_by(
            "-is_active", "payment_method", "billing_cycle"
        )
        return context


class PlanTierUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = PlanTier
    form_class = PlanTierForm
    template_name = "business_rule/plans/tier_form.html"
    modal_template_name = "business_rule/plans/tier_form_modal.html"
    modal_name = "plan-tier-edit"

    def get_success_url(self):
        return reverse_lazy("system:plan-tier-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Tier atualizado com sucesso.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar tier"
        context["form_action_label"] = "Salvar tier"
        return context


class PlanTierDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = PlanTier
    template_name = "business_rule/plans/tier_confirm_delete.html"
    success_url = reverse_lazy("system:plan-tier-list")
    context_object_name = "tier"

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                "Este tier não pode ser excluído porque possui preços cadastrados.",
            )
            return redirect("system:plan-tier-detail", pk=self.object.pk)
        messages.success(self.request, "Tier excluído com sucesso.")
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = build_plan_tier_usage(self.object)
        return context


class PlanPriceCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = PlanPrice
    form_class = PlanPriceForm
    template_name = "business_rule/plans/price_form.html"
    modal_template_name = "business_rule/plans/price_form_modal.html"
    modal_name = "plan-price-create"

    def dispatch(self, request, *args, **kwargs):
        self.tier = get_object_or_404(PlanTier, pk=kwargs["tier_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["locked_tier"] = self.tier
        return kwargs

    def form_valid(self, form):
        form.instance.tier = self.tier
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Preço criado com sucesso.")
        return response

    def get_success_url(self):
        return reverse_lazy("system:plan-tier-detail", kwargs={"pk": self.tier.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tier"] = self.tier
        context["form_title"] = f"Novo preço — {self.tier.display_name}"
        context["form_action_label"] = "Salvar preço"
        return context


class PlanPriceUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = PlanPrice
    form_class = PlanPriceForm
    template_name = "business_rule/plans/price_form.html"
    modal_template_name = "business_rule/plans/price_form_modal.html"
    modal_name = "plan-price-edit"

    def get_object(self, queryset=None):
        return get_plan_price_by_pk(self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["locked_tier"] = self.object.tier
        return kwargs

    def get_success_url(self):
        return reverse_lazy("system:plan-tier-detail", kwargs={"pk": self.object.tier_id})

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Preço atualizado com sucesso.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tier"] = self.object.tier
        context["form_title"] = "Editar preço"
        context["form_action_label"] = "Salvar preço"
        return context


class PlanPriceDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = PlanPrice
    template_name = "business_rule/plans/price_confirm_delete.html"
    context_object_name = "price"

    def get_object(self, queryset=None):
        return get_plan_price_by_pk(self.kwargs["pk"])

    def get_success_url(self):
        return reverse_lazy("system:plan-tier-detail", kwargs={"pk": self.object.tier_id})

    def form_valid(self, form):
        tier_pk = self.object.tier_id
        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                "Este preço não pode ser excluído porque possui assinaturas vinculadas. "
                "Desative-o na edição em vez de excluir.",
            )
            return redirect("system:plan-tier-detail", pk=tier_pk)
        messages.success(self.request, "Preço excluído com sucesso.")
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tier"] = self.object.tier
        context["usage"] = build_plan_price_usage(self.object)
        return context
