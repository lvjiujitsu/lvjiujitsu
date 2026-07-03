from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from system.constants import PortalCapability
from system.forms import (
    ClassCatalogDecisionForm,
    ExistingTeacherClassCatalogRequestForm,
)
from system.forms.class_request_forms import (
    ClassCatalogExtraScheduleFormSet,
    extract_extra_schedules,
)
from system.models import (
    ClassCatalogRequest,
    ClassCatalogRequestStatus,
    ClassCatalogRequestType,
)
from system.services.class_requests import (
    CLASS_CATALOG_DECISION_CAPABILITIES,
    approve_class_catalog_request,
    can_cancel_class_catalog_request,
    cancel_class_catalog_request,
    create_existing_teacher_class_request,
    reject_class_catalog_request,
)
from system.views.portal_mixins import PortalLoginRequiredMixin, PortalRoleRequiredMixin


class ExistingTeacherClassCatalogRequestCreateView(PortalRoleRequiredMixin, FormView):
    form_class = ExistingTeacherClassCatalogRequestForm
    template_name = "class_requests/request_form.html"
    success_url = reverse_lazy("system:home")
    required_capabilities = (PortalCapability.SUPPORT_CLASSES,)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["requester"] = getattr(self.request, "portal_person", None)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Solicitar turma ou horário"
        context["form_subtitle"] = "A gestão aprova antes de gravar no catálogo."
        context["back_url"] = reverse("system:home")
        context["extra_schedule_formset"] = kwargs.get(
            "extra_schedule_formset"
        ) or ClassCatalogExtraScheduleFormSet(prefix="extra_schedules")
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        extra_schedule_formset = ClassCatalogExtraScheduleFormSet(
            request.POST, prefix="extra_schedules"
        )
        if form.is_valid() and extra_schedule_formset.is_valid():
            return self._save(form, extra_schedule_formset)
        return self.render_to_response(
            self.get_context_data(form=form, extra_schedule_formset=extra_schedule_formset)
        )

    def _save(self, form, extra_schedule_formset):
        extra_schedules = extract_extra_schedules(extra_schedule_formset)
        try:
            create_existing_teacher_class_request(
                requester=getattr(self.request, "portal_person", None),
                request_type=form.cleaned_data["request_type"],
                class_group=form.cleaned_data.get("class_group"),
                class_category=form.cleaned_data.get("class_category"),
                display_name=form.cleaned_data.get("display_name", ""),
                weekday=form.cleaned_data["weekday"],
                training_style=form.cleaned_data["training_style"],
                start_time=form.cleaned_data["start_time"],
                duration_minutes=form.cleaned_data["duration_minutes"],
                default_capacity=form.cleaned_data.get("default_capacity") or 0,
                justification=form.cleaned_data["justification"],
                extra_schedules=extra_schedules,
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(
                self.get_context_data(form=form, extra_schedule_formset=extra_schedule_formset)
            )
        messages.success(self.request, "Solicitação de turma/horário enviada.")
        return redirect(self.success_url)


class PublicNewTeacherClassCatalogRequestCreateView(View):
    def dispatch(self, request, *args, **kwargs):
        return redirect(f"{reverse('system:register')}?profile=teacher_request")


class ClassCatalogRequestQueueView(PortalRoleRequiredMixin, ListView):
    model = ClassCatalogRequest
    template_name = "class_requests/request_list.html"
    context_object_name = "class_requests"
    required_capabilities = CLASS_CATALOG_DECISION_CAPABILITIES

    def get_queryset(self):
        queryset = ClassCatalogRequest.objects.select_related(
            "requester_person",
            "teacher_person",
            "target_class_group",
            "created_class_group",
            "class_category",
        )
        status = self.request.GET.get("status") or ""
        request_type = self.request.GET.get("request_type") or ""
        if status:
            queryset = queryset.filter(status=status)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = ClassCatalogRequestStatus.choices
        context["type_choices"] = ClassCatalogRequestType.choices
        context["current_status"] = self.request.GET.get("status") or ""
        context["current_type"] = self.request.GET.get("request_type") or ""
        return context


class ClassCatalogRequestDetailView(PortalRoleRequiredMixin, DetailView):
    model = ClassCatalogRequest
    template_name = "class_requests/request_detail.html"
    context_object_name = "class_request"
    required_capabilities = CLASS_CATALOG_DECISION_CAPABILITIES

    def get_queryset(self):
        return ClassCatalogRequest.objects.select_related(
            "requester_person",
            "teacher_person",
            "created_teacher",
            "target_class_group",
            "created_class_group",
            "class_category",
            "decided_by",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["decision_form"] = kwargs.get("decision_form") or ClassCatalogDecisionForm(
            catalog_request=self.object,
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
            cancel_class_catalog_request(
                self.object.pk,
                canceled_by=getattr(request, "portal_person", None),
            )
        except ValidationError as error:
            messages.error(request, "; ".join(getattr(error, "messages", None) or [str(error)]))
            return redirect("system:class-catalog-request-detail", pk=self.object.pk)
        messages.success(request, "Solicitação de turma/horário cancelada.")
        return redirect("system:class-catalog-request-detail", pk=self.object.pk)

    def _approve(self, request):
        form = ClassCatalogDecisionForm(request.POST, catalog_request=self.object)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(decision_form=form))
        try:
            approve_class_catalog_request(
                self.object.pk,
                approved_by=getattr(request, "portal_person", None),
                class_group=form.cleaned_data.get("class_group"),
                class_category=form.cleaned_data.get("class_category"),
                display_name=form.cleaned_data.get("display_name", ""),
                weekday=form.cleaned_data.get("weekday"),
                training_style=form.cleaned_data.get("training_style"),
                start_time=form.cleaned_data.get("start_time"),
                duration_minutes=form.cleaned_data.get("duration_minutes"),
                default_capacity=form.cleaned_data.get("default_capacity") or 0,
                decision_notes=form.cleaned_data.get("decision_notes", ""),
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(self.get_context_data(decision_form=form))
        messages.success(request, "Solicitação de turma/horário aprovada.")
        return redirect("system:class-catalog-request-detail", pk=self.object.pk)

    def _reject(self, request):
        notes = request.POST.get("decision_notes", "")
        form = ClassCatalogDecisionForm(request.POST, catalog_request=self.object)
        try:
            reject_class_catalog_request(
                self.object.pk,
                rejected_by=getattr(request, "portal_person", None),
                decision_notes=notes,
            )
        except ValidationError as error:
            _add_validation_error(form, error)
            return self.render_to_response(self.get_context_data(decision_form=form))
        messages.success(request, "Solicitação de turma/horário recusada.")
        return redirect("system:class-catalog-request-detail", pk=self.object.pk)


class ClassCatalogRequestSelfCancelView(PortalLoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        catalog_request = get_object_or_404(ClassCatalogRequest, pk=pk)
        actor = getattr(request, "portal_person", None)
        if not can_cancel_class_catalog_request(
            catalog_request,
            actor=actor,
            actor_capabilities=getattr(request, "portal_capabilities", set()),
        ):
            messages.error(request, "Você não pode cancelar esta solicitação.")
            return redirect("system:home")
        try:
            cancel_class_catalog_request(catalog_request.pk, canceled_by=actor)
        except ValidationError as error:
            messages.error(request, "; ".join(getattr(error, "messages", None) or [str(error)]))
            return redirect("system:home")
        messages.success(request, "Solicitação de turma/horário cancelada.")
        return redirect(request.POST.get("next") or "system:home")


def _add_validation_error(form, error):
    messages = getattr(error, "messages", None) or [str(error)]
    for message in messages:
        form.add_error(None, message)
