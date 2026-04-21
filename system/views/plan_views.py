from collections import OrderedDict

from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms.plan_forms import PlanForm
from system.models.plan import SubscriptionPlan
from system.services.plan_management import get_active_plans, get_plan_by_pk, get_plan_list
from system.views.person_views import AdministrativeRequiredMixin

CYCLE_ORDER = {"monthly": 1, "quarterly": 2, "semiannual": 3, "annual": 4}
CYCLE_LABELS = {
    "monthly": "Mensal",
    "quarterly": "Trimestral",
    "semiannual": "Semestral",
    "annual": "Anual",
}


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


class PlanCatalogView(ListView):
    template_name = "plans/plan_catalog.html"
    context_object_name = "plans"

    def get_queryset(self):
        return get_active_plans()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plan_groups"] = _build_plan_groups(context["plans"])
        return context


def _build_plan_groups(plans):
    grouped = OrderedDict()
    for plan in plans:
        section = "family" if plan.is_family_plan else "standard"
        cycle = plan.billing_cycle or "other"

        if section == "family":
            key = "family"
        else:
            key = f"standard:{cycle}"

        if key not in grouped:
            if section == "family":
                title = "Plano família"
                badge = "Família"
            else:
                cycle_label = CYCLE_LABELS.get(cycle, cycle.capitalize())
                title = f"Plano {cycle_label.lower()}"
                badge = cycle_label
            grouped[key] = {
                "key": key,
                "title": title,
                "section": section,
                "cycle": cycle if section == "standard" else None,
                "badge": badge,
                "plans": [],
            }
        grouped[key]["plans"].append(plan)

    def _sort_key(g):
        if g["section"] == "standard":
            return (0, CYCLE_ORDER.get(g["cycle"] or "", 99))
        return (1, 0)

    return sorted(grouped.values(), key=_sort_key)
