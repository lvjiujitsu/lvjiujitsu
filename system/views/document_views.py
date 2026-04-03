from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import CertificateLookupForm, LgpdRequestDecisionForm
from system.mixins import RoleRequiredMixin
from system.models import LgpdRequest
from system.selectors import find_certificate_by_code
from system.services.lgpd import process_lgpd_request


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class CertificateLookupView(TemplateView):
    template_name = "system/documents/certificate_lookup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or CertificateLookupForm(prefix="certificate")
        context["certificate_form"] = form
        context["certificate"] = kwargs.get("certificate")
        return context

    def post(self, request, *args, **kwargs):
        form = CertificateLookupForm(request.POST, prefix="certificate")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        certificate = find_certificate_by_code(form.cleaned_data["certificate_code"])
        return self.render_to_response(self.get_context_data(form=form, certificate=certificate))


class LgpdRequestManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/documents/lgpd_request_list.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        context["lgpd_requests"] = self._get_queryset()
        context["decision_form"] = kwargs.get("decision_form") or LgpdRequestDecisionForm(prefix="decision")
        return context

    def _get_queryset(self):
        queryset = LgpdRequest.objects.select_related("user", "processed_by")
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-created_at")


class LgpdRequestProcessView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        lgpd_request = get_object_or_404(self._get_queryset(), uuid=self.kwargs["uuid"])
        form = LgpdRequestDecisionForm(request.POST, prefix="decision")
        if not form.is_valid():
            return self._render_with_error(form)
        try:
            self._process_request(lgpd_request, form.cleaned_data)
        except ValidationError as exc:
            messages.error(request, exc.message)
            return redirect("system:lgpd-request-list")
        messages.success(request, "Solicitacao LGPD processada.")
        return redirect("system:lgpd-request-list")

    def _get_queryset(self):
        return LgpdRequest.objects.select_related("user")

    def _render_with_error(self, form):
        view = LgpdRequestManagementView()
        view.setup(self.request)
        return view.render_to_response(view.get_context_data(decision_form=form))

    def _process_request(self, lgpd_request, cleaned_data):
        process_lgpd_request(
            lgpd_request=lgpd_request,
            actor_user=self.request.user,
            approve=cleaned_data["decision"] == LgpdRequestDecisionForm.DECISION_APPROVE,
            processing_notes=cleaned_data["processing_notes"],
        )
