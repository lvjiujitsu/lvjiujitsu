from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from system.forms import LeadCaptureForm, TrialClassRequestPublicForm
from system.selectors.public_selectors import get_public_landing_context
from system.services.public.leads import capture_lead, create_trial_class_request


class HomeView(TemplateView):
    template_name = "system/public/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("system:portal-dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_public_landing_context())
        return context


class LeadCaptureView(FormView):
    form_class = LeadCaptureForm
    template_name = "system/public/lead_capture.html"
    success_url = reverse_lazy("system:lead-capture")

    def get_initial(self):
        initial = super().get_initial()
        requested_plan = self.request.GET.get("plan")
        if requested_plan:
            initial["requested_plan"] = requested_plan
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_public_landing_context())
        return context

    def form_valid(self, form):
        capture_lead(**form.cleaned_data)
        messages.success(self.request, "Recebemos seu interesse. Nossa equipe vai entrar em contato.")
        return redirect(self.get_success_url())


class TrialClassRequestView(FormView):
    form_class = TrialClassRequestPublicForm
    template_name = "system/public/trial_class_request.html"
    success_url = reverse_lazy("system:trial-class-request")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_public_landing_context())
        return context

    def form_valid(self, form):
        create_trial_class_request(**form.cleaned_data)
        messages.success(self.request, "Sua aula experimental foi solicitada com sucesso.")
        return redirect(self.get_success_url())
