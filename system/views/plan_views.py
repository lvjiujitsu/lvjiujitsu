from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms.plan_forms import PlanForm
from system.models.plan import SubscriptionPlan
from system.services.plan_management import get_plan_by_pk, get_plan_list
from system.views.person_views import AdministrativeRequiredMixin


class PlanListView(AdministrativeRequiredMixin, ListView):
    template_name = "plans/plan_list.html"
    context_object_name = "plans"

    def get_queryset(self):
        return get_plan_list()


class PlanCreateView(AdministrativeRequiredMixin, CreateView):
    model = SubscriptionPlan
    form_class = PlanForm
    template_name = "plans/plan_form.html"
    success_url = reverse_lazy("system:plan-list")


class PlanDetailView(AdministrativeRequiredMixin, DetailView):
    template_name = "plans/plan_detail.html"
    context_object_name = "plan"

    def get_object(self, queryset=None):
        return get_plan_by_pk(self.kwargs["pk"])


class PlanUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = SubscriptionPlan
    form_class = PlanForm
    template_name = "plans/plan_form.html"

    def get_success_url(self):
        return reverse_lazy("system:plan-detail", kwargs={"pk": self.object.pk})


class PlanDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = SubscriptionPlan
    template_name = "plans/plan_confirm_delete.html"
    success_url = reverse_lazy("system:plan-list")
    context_object_name = "plan"
