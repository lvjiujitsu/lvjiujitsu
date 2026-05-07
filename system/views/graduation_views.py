from django.contrib import messages
from django.shortcuts import redirect
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

from system.constants import ADMINISTRATIVE_PERSON_TYPE_CODES
from system.forms.graduation_forms import (
    BeltRankForm,
    GraduationForm,
    GraduationRuleForm,
)
from system.models import BeltRank, Graduation, GraduationRule
from system.selectors.graduation import get_graduation_overview
from system.services.graduation import compute_graduation_progress
from system.views.portal_mixins import PortalRoleRequiredMixin


class _AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES


class BeltRankListView(_AdministrativeRequiredMixin, ListView):
    model = BeltRank
    template_name = "graduation/belt_rank_list.html"
    context_object_name = "belt_ranks"

    def get_queryset(self):
        return BeltRank.objects.order_by("display_order", "display_name")


class BeltRankCreateView(_AdministrativeRequiredMixin, CreateView):
    model = BeltRank
    form_class = BeltRankForm
    template_name = "graduation/belt_rank_form.html"
    success_url = reverse_lazy("system:belt-rank-list")


class BeltRankUpdateView(_AdministrativeRequiredMixin, UpdateView):
    model = BeltRank
    form_class = BeltRankForm
    template_name = "graduation/belt_rank_form.html"
    success_url = reverse_lazy("system:belt-rank-list")


class BeltRankDetailView(_AdministrativeRequiredMixin, DetailView):
    model = BeltRank
    template_name = "graduation/belt_rank_detail.html"
    context_object_name = "belt_rank"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["graduation_rules"] = (
            GraduationRule.objects.filter(belt_rank=self.object).order_by("from_grade")
        )
        return context


class BeltRankDeleteView(_AdministrativeRequiredMixin, DeleteView):
    model = BeltRank
    template_name = "graduation/belt_rank_confirm_delete.html"
    success_url = reverse_lazy("system:belt-rank-list")
    context_object_name = "belt_rank"


class GraduationRuleListView(_AdministrativeRequiredMixin, ListView):
    model = GraduationRule
    template_name = "graduation/graduation_rule_list.html"
    context_object_name = "graduation_rules"

    def get_queryset(self):
        return (
            GraduationRule.objects.select_related("belt_rank")
            .order_by("belt_rank__display_order", "from_grade")
        )


class GraduationRuleCreateView(_AdministrativeRequiredMixin, CreateView):
    model = GraduationRule
    form_class = GraduationRuleForm
    template_name = "graduation/graduation_rule_form.html"
    success_url = reverse_lazy("system:graduation-rule-list")


class GraduationRuleUpdateView(_AdministrativeRequiredMixin, UpdateView):
    model = GraduationRule
    form_class = GraduationRuleForm
    template_name = "graduation/graduation_rule_form.html"
    success_url = reverse_lazy("system:graduation-rule-list")


class GraduationRuleDeleteView(_AdministrativeRequiredMixin, DeleteView):
    model = GraduationRule
    template_name = "graduation/graduation_rule_confirm_delete.html"
    success_url = reverse_lazy("system:graduation-rule-list")
    context_object_name = "graduation_rule"


class GraduationListView(_AdministrativeRequiredMixin, ListView):
    model = Graduation
    template_name = "graduation/graduation_list.html"
    context_object_name = "graduations"
    paginate_by = 30

    def get_queryset(self):
        return (
            Graduation.objects.select_related("person", "belt_rank", "awarded_by")
            .order_by("-awarded_at", "-created_at")
        )


class GraduationCreateView(_AdministrativeRequiredMixin, CreateView):
    model = Graduation
    form_class = GraduationForm
    template_name = "graduation/graduation_form.html"
    success_url = reverse_lazy("system:graduation-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Graduação registrada com sucesso.")
        return response


class GraduationDeleteView(_AdministrativeRequiredMixin, DeleteView):
    model = Graduation
    template_name = "graduation/graduation_confirm_delete.html"
    success_url = reverse_lazy("system:graduation-list")
    context_object_name = "graduation"


class GraduationOverviewView(_AdministrativeRequiredMixin, TemplateView):
    template_name = "graduation/graduation_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reference_date = timezone.localdate()
        context["reference_date"] = reference_date
        context["rows"] = get_graduation_overview(reference_date=reference_date)
        return context
