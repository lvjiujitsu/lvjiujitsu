import json
from decimal import Decimal

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
from system.models import Person
from system.models import PreRegistration
from system.services import asaas_client
from system.services.coupon import CouponError, apply_coupon, validate_coupon
from system.services.class_catalog import get_ibjjf_age_category_payload
from system.services.class_overview import get_registration_catalog_payload
from system.services.pre_registration import (
    finalize_pre_registration,
    get_pending_person_summary,
    get_registration_order_or_pre_registration_summary,
    mark_pre_registration_trial_requested,
    save_pre_registration_from_form,
)
from system.services.registration_checkout import (
    create_pre_registration_materials_payment,
    create_pre_registration_plan_payment,
    get_plan_catalog_payload,
    get_product_catalog_payload,
    create_product_only_order,
    gross_up_order_for_checkout,
    parse_selected_products,
    resolve_selected_product_items,
)
from system.services.registration_validation import validate_registration_step
from system.utils import ensure_formatted_cpf
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
            pre_registration_id = self.request.session.get("pending_pre_registration_id")
            if pre_registration_id:
                pr = PreRegistration.objects.filter(pk=pre_registration_id).first()
                if pr and pr.form_snapshot:
                    kwargs["initial"] = pr.form_snapshot
        return kwargs

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
        context["post_plan_payment_complete"] = self.request.session.get("post_plan_payment_complete", False)
        context["plan_is_trial"] = self.request.session.get("plan_is_trial", False)
        context["post_materials_payment_complete"] = self.request.session.get("post_materials_payment_complete", False)
        context["post_materials_skipped"] = self.request.session.get("post_materials_skipped", False)
        context["plan_order_json"] = json.dumps(
            get_registration_order_or_pre_registration_summary(self.request.session, "plan"),
            ensure_ascii=False,
        )
        context["materials_order_json"] = json.dumps(
            get_registration_order_or_pre_registration_summary(self.request.session, "materials"),
            ensure_ascii=False,
        )
        context["pending_person_json"] = json.dumps(
            self._get_pending_person_summary(), ensure_ascii=False
        )
        context["fee_config_json"] = json.dumps({
            "pixFixedFee": float(settings.ASAAS_PIX_FIXED_FEE),
            "creditCardPercentFee": float(settings.ASAAS_CREDIT_PERCENT_FEE),
            "creditCardFixedFee": float(settings.ASAAS_CREDIT_FIXED_FEE),
            "creditCardFeePassThrough": bool(settings.CREDIT_CARD_FEE_PASS_THROUGH),
            "pixFeePassThrough": bool(settings.PIX_FEE_PASS_THROUGH),
        }, ensure_ascii=False)
        return context

    def form_valid(self, form):
        pre_registration = save_pre_registration_from_form(
            self.request.session, self.request.POST, form.cleaned_data,
        )
        self.request.session["pending_pre_registration_id"] = pre_registration.pk
        self.request.session.pop("pending_registration_person_id", None)
        self.request.session.pop("post_plan_payment_complete", None)
        self.request.session.pop("post_materials_payment_complete", None)
        self.request.session.pop("post_materials_skipped", None)

        checkout_action = form.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
        if checkout_action == CheckoutAction.PAY_LATER:
            mark_pre_registration_trial_requested(pre_registration)
            self.request.session["post_plan_payment_complete"] = True
            self.request.session["plan_is_trial"] = True
            self.request.session.pop("plan_order_id", None)
            return redirect("system:register")

        try:
            invoice_url = create_pre_registration_plan_payment(
                pre_registration,
                checkout_action,
            )
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return redirect("system:register")
        except asaas_client.AsaasClientError:
            messages.error(
                self.request,
                "Pagamento Asaas indisponível no momento. Tente novamente em instantes.",
            )
            return redirect("system:register")
        pre_registration.mark_awaiting_payment()
        return redirect(invoice_url)

    def _get_pending_person_summary(self):
        return get_pending_person_summary(self.request.session)

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


class ValidateCouponView(View):
    def post(self, request, *args, **kwargs):
        from decimal import Decimal

        code = request.POST.get("coupon_code") or ""
        raw_total = request.POST.get("total") or "0"

        try:
            total = Decimal(raw_total)
        except Exception:
            return JsonResponse({"valid": False, "message": "Total inválido."}, status=400)

        try:
            coupon = validate_coupon(code)
        except CouponError as exc:
            return JsonResponse({"valid": False, "message": str(exc)})

        discounted_total, discount_amount = apply_coupon(coupon, total)
        from system.models.coupon import DiscountType
        label = (
            f"{coupon.discount_value}%"
            if coupon.discount_type == DiscountType.PERCENT
            else f"R$ {coupon.discount_value:.2f}".replace(".", ",")
        )
        return JsonResponse({
            "valid": True,
            "message": f"Cupom aplicado: {label} de desconto.",
            "discount_amount": str(discount_amount),
            "discounted_total": str(discounted_total),
            "coupon_code": coupon.code,
        })


class RegistrationCpfAvailabilityView(View):
    def get(self, request, *args, **kwargs):
        raw_cpf = request.GET.get("cpf", "")
        if not raw_cpf:
            return JsonResponse({"valid": False, "available": False, "error": "Informe o CPF."})
        try:
            cpf = ensure_formatted_cpf(raw_cpf)
        except ValueError as exc:
            return JsonResponse({"valid": False, "available": False, "error": str(exc)})
        exists = Person.objects.filter(cpf=cpf, is_active=True).exists()
        if exists:
            return JsonResponse({
                "valid": True,
                "available": False,
                "error": "CPF já cadastrado no sistema.",
            })
        return JsonResponse({"valid": True, "available": True, "error": ""})


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



class MaterialsCheckoutView(View):
    def post(self, request, *args, **kwargs):
        pre_registration_id = request.session.get("pending_pre_registration_id")
        if pre_registration_id:
            return self._post_for_pre_registration(request, pre_registration_id)

        person_id = request.session.get("pending_registration_person_id")
        if not person_id:
            return redirect("system:register")

        try:
            person = Person.objects.get(pk=person_id)
        except Person.DoesNotExist:
            return redirect("system:register")

        raw_payload = request.POST.get("selected_products_payload", "")
        selected = parse_selected_products(raw_payload)
        if not selected:
            request.session["post_materials_payment_complete"] = True
            return redirect("system:register")

        try:
            items = resolve_selected_product_items(selected)
        except ValueError:
            messages.error(request, "Selecione apenas materiais válidos com estoque disponível.")
            return redirect("system:register")

        order = create_product_only_order(person, items)
        if order is None:
            request.session["post_materials_payment_complete"] = True
            return redirect("system:register")

        request.session["pending_checkout_order_id"] = order.pk
        checkout_action = request.POST.get("checkout_action") or CheckoutAction.PAY_LATER
        gross_up_order_for_checkout(order, checkout_action)
        if checkout_action == CheckoutAction.ASAAS_CARD:
            return redirect("system:asaas-card-create", order_id=order.pk)
        if checkout_action == CheckoutAction.PIX:
            return redirect("system:asaas-pix-create", order_id=order.pk)

        request.session["post_materials_payment_complete"] = True
        request.session["materials_order_id"] = order.pk
        return redirect("system:register")

    def _post_for_pre_registration(self, request, pre_registration_id):
        pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if pre_registration is None:
            return redirect("system:register")

        raw_payload = request.POST.get("selected_products_payload", "")
        selected = parse_selected_products(raw_payload)
        snapshot = pre_registration.form_snapshot or {}
        snapshot["selected_products_payload"] = raw_payload or "[]"
        snapshot["materials_checkout_action"] = request.POST.get("checkout_action") or CheckoutAction.PAY_LATER
        pre_registration.form_snapshot = snapshot
        pre_registration.save(update_fields=["form_snapshot", "updated_at"])

        if not selected:
            request.session["post_materials_skipped"] = True
            request.session.pop("post_materials_payment_complete", None)
            return redirect("system:register")

        try:
            items = resolve_selected_product_items(selected)
        except ValueError:
            messages.error(request, "Selecione apenas materiais válidos com estoque disponível.")
            return redirect("system:register")

        checkout_action = request.POST.get("checkout_action") or CheckoutAction.PAY_LATER
        if checkout_action == CheckoutAction.PAY_LATER:
            request.session["post_materials_skipped"] = True
            request.session.pop("post_materials_payment_complete", None)
            return redirect("system:register")

        try:
            invoice_url = create_pre_registration_materials_payment(
                pre_registration,
                items,
                checkout_action,
            )
        except asaas_client.AsaasClientError:
            messages.error(
                request,
                "Pagamento Asaas dos materiais indisponível no momento. Tente novamente em instantes.",
            )
            return redirect("system:register")
        return redirect(invoice_url)


class ResetRegistrationView(View):
    """Limpa estado de cadastro da sessão e redireciona para /register/ limpo."""

    _SESSION_KEYS = (
        "pending_pre_registration_id",
        "pending_registration_person_id",
        "post_plan_payment_complete",
        "post_materials_payment_complete",
        "post_materials_skipped",
        "plan_order_id",
        "materials_order_id",
        "plan_is_trial",
    )

    def get(self, request, *args, **kwargs):
        request.session.flush()
        return redirect("system:register")


class FinalizeRegistrationView(View):
    """Ativa person.is_active=True, faz login e redireciona para dashboard."""

    def post(self, request, *args, **kwargs):
        pre_registration_id = request.session.get("pending_pre_registration_id")
        if pre_registration_id:
            return self._finalize_pre_registration(request, pre_registration_id)

        person_id = request.session.get("pending_registration_person_id")
        if not person_id:
            return redirect("system:register")

        try:
            person = Person.objects.select_related("access_account").get(pk=person_id)
        except Person.DoesNotExist:
            return redirect("system:register")

        if not person.is_active:
            person.is_active = True
            person.save(update_fields=["is_active", "updated_at"])

        portal_account = getattr(person, "access_account", None)
        if portal_account and not portal_account.is_active:
            portal_account.is_active = True
            portal_account.save(update_fields=["is_active", "updated_at"])

        for key in (
            "pending_registration_person_id",
            "post_plan_payment_complete",
            "post_materials_payment_complete",
            "plan_order_id",
            "materials_order_id",
        ):
            request.session.pop(key, None)

        if portal_account:
            login_portal_identity(request, portal_account=portal_account)

        messages.success(request, "Cadastro finalizado com sucesso! Seja bem-vindo.")
        return redirect("system:dashboard-redirect")

    def _finalize_pre_registration(self, request, pre_registration_id):
        pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if pre_registration is None:
            return redirect("system:register")

        result = finalize_pre_registration(pre_registration)
        if result["already_finalized"]:
            return redirect("system:dashboard-redirect")
        if not result["ok"]:
            messages.error(request, result["error"])
            return redirect("system:register")

        for key in (
            "pending_pre_registration_id",
            "pending_registration_person_id",
            "post_plan_payment_complete",
            "post_materials_payment_complete",
            "post_materials_skipped",
            "plan_order_id",
            "materials_order_id",
            "plan_is_trial",
        ):
            request.session.pop(key, None)

        portal_account = result["portal_account"]
        if portal_account:
            login_portal_identity(request, portal_account=portal_account)
        messages.success(request, "Cadastro finalizado com sucesso! Seja bem-vindo.")
        return redirect("system:dashboard-redirect")
