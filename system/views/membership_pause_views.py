from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, ListView

from system.constants import STUDENT_PORTAL_PERSON_TYPE_CODES
from system.forms import MembershipPauseDecisionForm, MembershipPauseRequestForm
from system.models.membership import (
    MembershipPauseRequest,
    MembershipPauseRequestKind,
    MembershipPauseRequestStatus,
)
from system.services.membership import get_active_membership
from system.services.membership_pause import (
    PAUSE_DECISION_CAPABILITIES,
    approve_pause_request,
    cancel_pause_request,
    create_pause_request,
    get_self_service_quota_summary,
    reject_pause_request,
)
from system.views.portal_mixins import PortalRoleRequiredMixin


class MembershipPauseRequestCreateView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES

    def post(self, request):
        person = request.portal_person
        membership = get_active_membership(person)
        if not membership:
            return JsonResponse(
                {"success": False, "error": "Você não possui uma assinatura ativa."},
                status=400,
            )

        form = MembershipPauseRequestForm(request.POST)
        if not form.is_valid():
            first_error = next(iter(form.errors.values()))[0]
            return JsonResponse({"success": False, "error": first_error}, status=400)

        try:
            create_pause_request(
                membership,
                kind=form.cleaned_data["kind"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
                reason_note=form.cleaned_data.get("reason_note", ""),
            )
        except ValidationError as exc:
            return JsonResponse(
                {"success": False, "error": "; ".join(getattr(exc, "messages", None) or [str(exc)])},
                status=400,
            )
        return JsonResponse(
            {
                "success": True,
                "message": "Solicitação de pausa enviada — aguardando aprovação do administrativo.",
            }
        )


class MembershipPauseQuotaView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES

    def get(self, request):
        person = request.portal_person
        membership = get_active_membership(person)
        if not membership:
            return JsonResponse({"success": False, "error": "Sem assinatura ativa."}, status=400)
        summary = get_self_service_quota_summary(membership)
        return JsonResponse(
            {
                "success": True,
                "used_days": summary["used_days"],
                "remaining_days": summary["remaining_days"],
                "quota_days": summary["quota_days"],
                "window_start": summary["window_start"].isoformat(),
                "window_end": summary["window_end"].isoformat(),
            }
        )


class MembershipPauseRequestQueueView(PortalRoleRequiredMixin, ListView):
    model = MembershipPauseRequest
    template_name = "membership_pauses/pause_request_list.html"
    context_object_name = "pause_requests"
    required_capabilities = PAUSE_DECISION_CAPABILITIES

    def get_queryset(self):
        queryset = MembershipPauseRequest.objects.select_related(
            "membership", "membership__person", "decided_by"
        )
        status = self.request.GET.get("status") or ""
        kind = self.request.GET.get("kind") or ""
        cpf = self.request.GET.get("cpf") or ""
        date_from = self.request.GET.get("date_from") or ""
        date_to = self.request.GET.get("date_to") or ""
        if status:
            queryset = queryset.filter(status=status)
        if kind:
            queryset = queryset.filter(kind=kind)
        if cpf:
            queryset = queryset.filter(membership__person__cpf__icontains=cpf)
        parsed_date_from = parse_date(date_from) if date_from else None
        parsed_date_to = parse_date(date_to) if date_to else None
        if parsed_date_from:
            queryset = queryset.filter(created_at__date__gte=parsed_date_from)
        if parsed_date_to:
            queryset = queryset.filter(created_at__date__lte=parsed_date_to)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = MembershipPauseRequestStatus.choices
        context["kind_choices"] = MembershipPauseRequestKind.choices
        context["current_status"] = self.request.GET.get("status") or ""
        context["current_kind"] = self.request.GET.get("kind") or ""
        context["current_cpf"] = self.request.GET.get("cpf") or ""
        context["current_date_from"] = self.request.GET.get("date_from") or ""
        context["current_date_to"] = self.request.GET.get("date_to") or ""
        return context


class MembershipPauseRequestDetailView(PortalRoleRequiredMixin, DetailView):
    model = MembershipPauseRequest
    template_name = "membership_pauses/pause_request_detail.html"
    context_object_name = "pause_request"
    required_capabilities = PAUSE_DECISION_CAPABILITIES

    def get_queryset(self):
        return MembershipPauseRequest.objects.select_related(
            "membership", "membership__person", "decided_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["decision_form"] = kwargs.get("decision_form") or MembershipPauseDecisionForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        if action == "reject":
            return self._reject(request)
        if action == "cancel":
            return self._cancel(request)
        return self._approve(request)

    def _approve(self, request):
        form = MembershipPauseDecisionForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(decision_form=form))
        try:
            approve_pause_request(
                self.object.pk,
                approved_by=getattr(request, "portal_person", None),
                decision_notes=form.cleaned_data.get("decision_notes", ""),
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(self.get_context_data(decision_form=form))
        except Exception as error:
            form.add_error(None, str(error))
            return self.render_to_response(self.get_context_data(decision_form=form))
        messages.success(request, "Pausa de mensalidade aprovada.")
        return redirect("system:membership-pause-request-detail", pk=self.object.pk)

    def _reject(self, request):
        notes = request.POST.get("decision_notes", "")
        form = MembershipPauseDecisionForm(request.POST)
        try:
            reject_pause_request(
                self.object.pk,
                rejected_by=getattr(request, "portal_person", None),
                decision_notes=notes,
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(self.get_context_data(decision_form=form))
        messages.success(request, "Pausa de mensalidade recusada.")
        return redirect("system:membership-pause-request-detail", pk=self.object.pk)

    def _cancel(self, request):
        try:
            cancel_pause_request(
                self.object.pk,
                canceled_by=getattr(request, "portal_person", None),
            )
        except ValidationError as error:
            messages.error(request, "; ".join(getattr(error, "messages", None) or [str(error)]))
            return redirect("system:membership-pause-request-detail", pk=self.object.pk)
        messages.success(request, "Solicitação de pausa cancelada.")
        return redirect("system:membership-pause-request-detail", pk=self.object.pk)


def _add_validation_error(form, error):
    error_messages = getattr(error, "messages", None) or [str(error)]
    for message in error_messages:
        form.add_error(None, message)
