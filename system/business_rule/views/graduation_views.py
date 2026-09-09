from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from system.business_rule.forms.graduation_forms import (
    BeltRankForm,
    GraduationForm,
    GraduationRuleForm,
)
from system.business_rule.models import BeltRank, Graduation, GraduationRule
from system.business_rule.selectors.graduation import get_graduation_overview
from system.business_rule.views.person_views import ModalFormMixin
from system.business_rule.access import AdministrativeRequiredMixin


class BeltRankListView(AdministrativeRequiredMixin, ListView):
    model = BeltRank
    template_name = "business_rule/graduation/belt_rank_list.html"
    context_object_name = "belt_ranks"

    def get_queryset(self):
        return BeltRank.objects.order_by("display_order", "display_name")


class BeltRankCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = BeltRank
    form_class = BeltRankForm
    template_name = "business_rule/graduation/belt_rank_form.html"
    modal_name = "belt-rank-create"
    success_url = reverse_lazy("system:belt-rank-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Nova faixa"
        return context


class BeltRankUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = BeltRank
    form_class = BeltRankForm
    template_name = "business_rule/graduation/belt_rank_form.html"
    modal_name = "belt-rank-edit"
    success_url = reverse_lazy("system:belt-rank-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar faixa"
        return context


class BeltRankDetailView(AdministrativeRequiredMixin, DetailView):
    model = BeltRank
    template_name = "business_rule/graduation/belt_rank_detail.html"
    context_object_name = "belt_rank"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["graduation_rules"] = (
            GraduationRule.objects.filter(belt_rank=self.object).order_by("from_grade")
        )
        return context


class BeltRankDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = BeltRank
    template_name = "business_rule/graduation/belt_rank_confirm_delete.html"
    success_url = reverse_lazy("system:belt-rank-list")
    context_object_name = "belt_rank"


class GraduationRuleListView(AdministrativeRequiredMixin, ListView):
    model = GraduationRule
    template_name = "business_rule/graduation/graduation_rule_list.html"
    context_object_name = "graduation_rules"

    def get_queryset(self):
        return (
            GraduationRule.objects.select_related("belt_rank")
            .order_by("belt_rank__display_order", "from_grade")
        )


class GraduationRuleCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = GraduationRule
    form_class = GraduationRuleForm
    template_name = "business_rule/graduation/graduation_rule_form.html"
    modal_name = "graduation-rule-create"
    success_url = reverse_lazy("system:graduation-rule-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Nova regra"
        return context


class GraduationRuleUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = GraduationRule
    form_class = GraduationRuleForm
    template_name = "business_rule/graduation/graduation_rule_form.html"
    modal_name = "graduation-rule-edit"
    success_url = reverse_lazy("system:graduation-rule-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar regra"
        return context


class GraduationRuleDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = GraduationRule
    template_name = "business_rule/graduation/graduation_rule_confirm_delete.html"
    success_url = reverse_lazy("system:graduation-rule-list")
    context_object_name = "graduation_rule"


class GraduationListView(AdministrativeRequiredMixin, ListView):
    model = Graduation
    template_name = "business_rule/graduation/graduation_list.html"
    context_object_name = "graduations"
    paginate_by = 30

    def get_queryset(self):
        return (
            Graduation.objects.select_related("person", "belt_rank", "awarded_by")
            .order_by("-awarded_at", "-created_at")
        )


class GraduationCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = Graduation
    form_class = GraduationForm
    template_name = "business_rule/graduation/graduation_form.html"
    modal_name = "graduation-create"
    success_url = reverse_lazy("system:graduation-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.is_modal():
            messages.success(self.request, "Graduação registrada com sucesso.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Nova graduação"
        return context


class GraduationDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Graduation
    template_name = "business_rule/graduation/graduation_confirm_delete.html"
    success_url = reverse_lazy("system:graduation-list")
    context_object_name = "graduation"


class GraduationOverviewView(AdministrativeRequiredMixin, TemplateView):
    template_name = "business_rule/graduation/graduation_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reference_date = timezone.localdate()
        context["reference_date"] = reference_date
        context["rows"] = get_graduation_overview(reference_date=reference_date)
        return context
