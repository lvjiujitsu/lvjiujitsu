import json

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from system.forms import (
    PortalAuthenticationForm,
    PortalPasswordResetRequestForm,
    PortalRegistrationForm,
    PortalSetPasswordForm,
)
from system.constants import CheckoutAction
from system.services.class_catalog import get_ibjjf_age_category_payload
from system.services.class_overview import get_registration_catalog_payload
from system.services.registration_checkout import get_plan_catalog_payload, get_product_catalog_payload
from system.services.registration_validation import validate_registration_step
from system.services.trial_access import grant_trial_for_order
from system.services import (
    authenticate_portal_identity,
    create_password_reset_token,
    get_valid_password_reset_token,
    login_portal_identity,
    logout_portal_identity,
    reset_portal_password,
)


class PortalRegisterView(FormView):
    form_class = PortalRegistrationForm
    template_name = "login/register.html"
    success_url = reverse_lazy("system:login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["registration_initial_step"] = self._get_initial_step(form)
        context["selected_other_type_code"] = form["other_type_code"].value() or ""
        context["registration_catalog_json"] = json.dumps(
            get_registration_catalog_payload(), ensure_ascii=False
        )
        context["ibjjf_categories_json"] = json.dumps(
            get_ibjjf_age_category_payload(), ensure_ascii=False
        )
        context["plan_catalog_json"] = json.dumps(
            get_plan_catalog_payload(), ensure_ascii=False
        )
        context["product_catalog_json"] = json.dumps(
            get_product_catalog_payload(), ensure_ascii=False
        )
        return context

    def form_valid(self, form):
        created_people = form.save()
        order = created_people.pop("order", None)
        created_labels = []
        for value in created_people.values():
            if isinstance(value, list):
                created_labels.extend(person.full_name for person in value)
            else:
                created_labels.append(value.full_name)
        unique_labels = list(dict.fromkeys(created_labels))
        messages.success(
            self.request,
            f"Cadastro registrado com sucesso para: {', '.join(unique_labels)}.",
        )
        if order is not None and order.total and order.total > 0:
            self.request.session["pending_checkout_order_id"] = order.pk
            checkout_action = form.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
            if checkout_action == CheckoutAction.STRIPE:
                return redirect("system:stripe-checkout", order_id=order.pk)
            if checkout_action == CheckoutAction.PIX:
                return redirect("system:asaas-pix-create", order_id=order.pk)

            grant_trial_for_order(
                order,
                notes="Cadastro concluído sem pagamento imediato.",
            )
            messages.warning(
                self.request,
                "Cadastro concluído sem pagamento. "
                f"Você tem {settings.TRIAL_ACCESS_DEFAULT_CLASSES} aula(s) experimental(is) "
                "liberada e pode pagar depois para ativar sua mensalidade.",
            )
            return redirect("system:login")
        return super().form_valid(form)

    def _get_initial_step(self, form):
        if not form.is_bound or not form.errors:
            return 1

        medical_fields = {
            "holder_blood_type",
            "holder_allergies",
            "holder_injuries",
            "holder_emergency_contact",
            "holder_has_martial_art",
            "holder_martial_art",
            "holder_martial_art_graduation",
            "holder_jiu_jitsu_belt",
            "holder_jiu_jitsu_stripes",
            "dependent_blood_type",
            "dependent_allergies",
            "dependent_injuries",
            "dependent_emergency_contact",
            "dependent_has_martial_art",
            "dependent_martial_art",
            "dependent_martial_art_graduation",
            "dependent_jiu_jitsu_belt",
            "dependent_jiu_jitsu_stripes",
            "student_blood_type",
            "student_allergies",
            "student_injuries",
            "student_emergency_contact",
            "student_has_martial_art",
            "student_martial_art",
            "student_martial_art_graduation",
            "student_jiu_jitsu_belt",
            "student_jiu_jitsu_stripes",
        }
        class_fields = {
            "holder_class_groups",
            "dependent_class_groups",
            "student_class_groups",
            "extra_dependents_payload",
        }
        registration_fields = {
            "registration_profile",
            "include_dependent",
            "other_type_code",
        }

        error_fields = set(form.errors.keys())
        if error_fields & medical_fields:
            return 4
        if error_fields & class_fields:
            return 3
        if error_fields - registration_fields:
            return 2
        return 1


class RegistrationStepValidationView(View):
    def post(self, request, *args, **kwargs):
        errors = validate_registration_step(request.POST)
        return JsonResponse({"valid": not errors, "errors": errors})


class PortalLoginView(FormView):
    form_class = PortalAuthenticationForm
    template_name = "login/login_form.html"

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "portal_account", None) is not None or getattr(
            request, "portal_is_technical_admin", False
        ):
            return redirect("system:dashboard-redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        identity = authenticate_portal_identity(
            identifier=form.cleaned_data["identifier"],
            password=form.cleaned_data["password"],
        )

        if identity is None:
            form.add_error(None, "CPF, acesso técnico ou senha inválidos.")
            return self.form_invalid(form)

        if identity.get("blocked_reason") == "payment_pending":
            pending_order = identity.get("pending_order")
            if pending_order is not None:
                self.request.session["pending_checkout_order_id"] = pending_order.pk
                messages.info(
                    self.request,
                    "Seu cadastro está aguardando a confirmação do pagamento. "
                    "Vamos redirecioná-lo para concluir agora.",
                )
                return redirect(
                    "system:payment-checkout", order_id=pending_order.pk
                )
            form.add_error(
                None,
                "Seu cadastro está aguardando a confirmação do pagamento. "
                "Conclua o pagamento para acessar o sistema.",
            )
            return self.form_invalid(form)

        login_portal_identity(
            self.request,
            portal_account=identity["portal_account"],
            technical_admin_user=identity["technical_admin_user"],
        )
        redirect_to = self.request.POST.get("next") or self.request.GET.get("next")
        return redirect(redirect_to or reverse("system:dashboard-redirect"))


class PortalLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout_portal_identity(request)
        return redirect("system:root")

    def post(self, request, *args, **kwargs):
        logout_portal_identity(request)
        return redirect("system:root")


class PortalPasswordResetView(FormView):
    form_class = PortalPasswordResetRequestForm
    template_name = "login/password_reset_form.html"
    success_url = reverse_lazy("system:password-reset-done")

    def form_valid(self, form):
        create_password_reset_token(form.cleaned_data["cpf"], self.request)
        return super().form_valid(form)


class PortalPasswordResetDoneView(TemplateView):
    template_name = "login/password_reset_done.html"


class PortalPasswordResetConfirmView(FormView):
    form_class = PortalSetPasswordForm
    template_name = "login/password_reset_confirm.html"
    success_url = reverse_lazy("system:password-reset-complete")

    def dispatch(self, request, *args, **kwargs):
        self.reset_token = get_valid_password_reset_token(kwargs["token"])
        if self.reset_token is None:
            raise Http404("Token de redefinição inválido.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        reset_portal_password(self.reset_token, form.cleaned_data["new_password1"])
        return super().form_valid(form)


class PortalPasswordResetCompleteView(TemplateView):
    template_name = "login/password_reset_complete.html"


class ChromeDevtoolsProbeView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=204, content_type="application/json")
