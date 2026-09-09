from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from system.business_rule.forms import AdministrativeAccessDecisionForm, AdministrativeAccessRequestForm
from system.business_rule.models import (
    AdministrativeAccessRequest,
    AdministrativeAccessRequestOrigin,
    AdministrativeAccessRequestStatus,
)
from system.business_rule.services.access_requests import (
    ADMINISTRATIVE_ACCESS_DECISION_CAPABILITIES,
    approve_administrative_access_request,
    can_cancel_administrative_access_request,
    cancel_administrative_access_request,
    reject_administrative_access_request,
)
from system.business_rule.access import (
    PortalLoginRequiredMixin,
    PortalRoleRequiredMixin,
    portal_capabilities,
    portal_person,
)


class PublicAdministrativeAccessRequestCreateView(View):
    def dispatch(self, request, *args, **kwargs):
        return redirect(f"{reverse('system:register')}?profile=administrative_request")


class PortalAdministrativeAccessRequestCreateView(PortalLoginRequiredMixin, FormView):
    form_class = AdministrativeAccessRequestForm
    template_name = "business_rule/access_requests/request_form.html"
    success_url = reverse_lazy("system:home")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["origin"] = AdministrativeAccessRequestOrigin.PORTAL
        kwargs["portal_person"] = portal_person(self.request)
        kwargs["require_password"] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Solicitar acesso administrativo"
        context["form_subtitle"] = "Seu perfil atual continua igual até a aprovação."
        context["back_url"] = reverse("system:home")
        return context

    def form_valid(self, form):
        try:
            form.save()
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.form_invalid(form)
        messages.success(self.request, "Solicitação administrativa enviada.")
        return super().form_valid(form)


class AdministrativeAccessRequestQueueView(PortalRoleRequiredMixin, ListView):
    model = AdministrativeAccessRequest
    template_name = "business_rule/access_requests/request_list.html"
    context_object_name = "access_requests"
    required_capabilities = ADMINISTRATIVE_ACCESS_DECISION_CAPABILITIES

    def get_queryset(self):
        queryset = AdministrativeAccessRequest.objects.select_related(
            "person",
            "approved_person",
            "decided_by",
        )
        status = self.request.GET.get("status") or ""
        origin = self.request.GET.get("origin") or ""
        cpf = self.request.GET.get("cpf") or ""
        date_from = self.request.GET.get("date_from") or ""
        date_to = self.request.GET.get("date_to") or ""
        if status:
            queryset = queryset.filter(status=status)
        if origin:
            queryset = queryset.filter(origin=origin)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        parsed_date_from = parse_date(date_from) if date_from else None
        parsed_date_to = parse_date(date_to) if date_to else None
        if parsed_date_from:
            queryset = queryset.filter(created_at__date__gte=parsed_date_from)
        if parsed_date_to:
            queryset = queryset.filter(created_at__date__lte=parsed_date_to)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = AdministrativeAccessRequestStatus.choices
        context["origin_choices"] = AdministrativeAccessRequestOrigin.choices
        context["current_status"] = self.request.GET.get("status") or ""
        context["current_origin"] = self.request.GET.get("origin") or ""
        context["current_cpf"] = self.request.GET.get("cpf") or ""
        context["current_date_from"] = self.request.GET.get("date_from") or ""
        context["current_date_to"] = self.request.GET.get("date_to") or ""
        return context


class AdministrativeAccessRequestDetailView(PortalRoleRequiredMixin, DetailView):
    model = AdministrativeAccessRequest
    template_name = "business_rule/access_requests/request_detail.html"
    context_object_name = "access_request"
    required_capabilities = ADMINISTRATIVE_ACCESS_DECISION_CAPABILITIES

    def get_queryset(self):
        return AdministrativeAccessRequest.objects.select_related(
            "person",
            "approved_person",
            "decided_by",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["decision_form"] = kwargs.get("decision_form") or AdministrativeAccessDecisionForm(
            access_request=self.object,
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action == "reject":
            return self._reject(request)
        if action == "cancel":
            return self._cancel(request)
        return self._approve(request)

    def _cancel(self, request):
        try:
            cancel_administrative_access_request(
                self.object.pk,
                canceled_by=portal_person(request),
            )
        except ValidationError as error:
            messages.error(request, "; ".join(getattr(error, "messages", None) or [str(error)]))
            return redirect("system:administrative-access-request-detail", pk=self.object.pk)
        messages.success(request, "Solicitação administrativa cancelada.")
        return redirect("system:administrative-access-request-detail", pk=self.object.pk)

    def _approve(self, request):
        form = AdministrativeAccessDecisionForm(
            request.POST,
            access_request=self.object,
        )
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(decision_form=form))
        try:
            approve_administrative_access_request(
                self.object.pk,
                approved_by=portal_person(request),
                approved_role_ids=[role.pk for role in form.cleaned_data["approved_roles"]],
                grant_full_administrative=form.cleaned_data["grant_full_administrative"],
                decision_notes=form.cleaned_data.get("decision_notes", ""),
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(self.get_context_data(decision_form=form))
        messages.success(request, "Solicitação administrativa aprovada.")
        return redirect("system:administrative-access-request-detail", pk=self.object.pk)

    def _reject(self, request):
        notes = request.POST.get("decision_notes", "")
        form = AdministrativeAccessDecisionForm(
            request.POST,
            access_request=self.object,
        )
        try:
            reject_administrative_access_request(
                self.object.pk,
                rejected_by=portal_person(request),
                decision_notes=notes,
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(self.get_context_data(decision_form=form))
        messages.success(request, "Solicitação administrativa recusada.")
        return redirect("system:administrative-access-request-detail", pk=self.object.pk)


class AdministrativeAccessRequestSelfCancelView(PortalLoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        access_request = get_object_or_404(AdministrativeAccessRequest, pk=pk)
        actor = portal_person(request)
        if not can_cancel_administrative_access_request(
            access_request,
            actor=actor,
            actor_capabilities=portal_capabilities(request),
        ):
            messages.error(request, "Você não pode cancelar esta solicitação.")
            return redirect("system:home")
        try:
            cancel_administrative_access_request(access_request.pk, canceled_by=actor)
        except ValidationError as error:
            messages.error(request, "; ".join(getattr(error, "messages", None) or [str(error)]))
            return redirect("system:home")
        messages.success(request, "Solicitação administrativa cancelada.")
        return redirect(request.POST.get("next") or "system:home")


def _add_validation_error(form, error):
    entries = getattr(error, "messages", None) or [str(error)]
    for entry in entries:
        form.add_error(None, entry)
