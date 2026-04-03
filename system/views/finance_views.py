from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.forms import (
    EnrollmentPauseCreateForm,
    FinancialBenefitForm,
    FinancialPlanForm,
    LocalSubscriptionCreateForm,
    MonthlyInvoiceCreateForm,
    PaymentProofReviewForm,
    PaymentProofUploadForm,
)
from system.mixins import RoleRequiredMixin
from system.selectors import (
    get_checkout_allowed_subscriptions,
    get_financial_benefits_queryset,
    get_financial_plans_queryset,
    get_invoices_queryset,
    get_pauses_queryset,
    get_payment_proofs_queryset,
    get_responsible_invoices_queryset,
    get_subscriptions_queryset,
)
from system.services.finance import (
    create_enrollment_pause,
    create_local_subscription,
    issue_monthly_invoice,
    mark_invoice_overdue,
    mark_invoice_paid,
    resume_enrollment_pause,
    review_payment_proof,
    upload_payment_proof,
)
from system.services.payments import is_stripe_configured


ADMIN_ROLE_CODES = (ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO)


class FinanceManagementView(RoleRequiredMixin, TemplateView):
    template_name = "system/finance/finance_dashboard.html"
    required_roles = ADMIN_ROLE_CODES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_collections())
        context.update(self._build_forms(kwargs))
        context["invoice_status_filter"] = self.request.GET.get("invoice_status", "")
        context["proof_status_filter"] = self.request.GET.get("proof_status", "")
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        handlers = {
            "plan": self._handle_plan_create,
            "benefit": self._handle_benefit_create,
            "subscription": self._handle_subscription_create,
            "invoice": self._handle_invoice_create,
            "pause": self._handle_pause_create,
        }
        return handlers.get(action, self._invalid_action)()

    def _build_collections(self):
        return {
            "plans": get_financial_plans_queryset(),
            "benefits": get_financial_benefits_queryset(),
            "subscriptions": get_subscriptions_queryset(),
            "invoices": self._get_invoices(),
            "pauses": get_pauses_queryset(),
            "payment_proofs": self._get_payment_proofs(),
        }

    def _build_forms(self, overrides):
        return {
            "plan_form": overrides.get("plan_form") or FinancialPlanForm(prefix="plan"),
            "benefit_form": overrides.get("benefit_form") or FinancialBenefitForm(prefix="benefit"),
            "subscription_form": overrides.get("subscription_form") or LocalSubscriptionCreateForm(prefix="subscription"),
            "invoice_form": overrides.get("invoice_form") or MonthlyInvoiceCreateForm(prefix="invoice"),
            "pause_form": overrides.get("pause_form") or EnrollmentPauseCreateForm(prefix="pause"),
        }

    def _get_invoices(self):
        queryset = get_invoices_queryset()
        status = self.request.GET.get("invoice_status")
        return queryset.filter(status=status) if status else queryset

    def _get_payment_proofs(self):
        queryset = get_payment_proofs_queryset()
        status = self.request.GET.get("proof_status")
        return queryset.filter(status=status) if status else queryset

    def _handle_plan_create(self):
        return self._persist_model_form(
            FinancialPlanForm,
            prefix="plan",
            success_message="Plano financeiro salvo.",
            form_key="plan_form",
        )

    def _handle_benefit_create(self):
        return self._persist_model_form(
            FinancialBenefitForm,
            prefix="benefit",
            success_message="Beneficio financeiro salvo.",
            form_key="benefit_form",
        )

    def _persist_model_form(self, form_class, *, prefix, success_message, form_key):
        form = form_class(self.request.POST, prefix=prefix)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(**{form_key: form}))
        form.save()
        messages.success(self.request, success_message)
        return redirect("system:finance-dashboard")

    def _handle_subscription_create(self):
        form = LocalSubscriptionCreateForm(self.request.POST, prefix="subscription")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(subscription_form=form))
        payload = {
            "plan": form.cleaned_data["plan"],
            "responsible_cpf": form.cleaned_data["responsible_cpf"],
            "responsible_full_name": form.cleaned_data["responsible_full_name"],
            "responsible_email": form.cleaned_data["responsible_email"],
            "student_profiles": form.cleaned_data["students"],
            "benefit": form.cleaned_data["benefit"],
            "primary_student": form.cleaned_data["primary_student"],
            "status": form.cleaned_data["status"],
            "notes": form.cleaned_data["notes"],
        }
        create_local_subscription(**payload)
        messages.success(self.request, "Assinatura local criada.")
        return redirect("system:finance-dashboard")

    def _handle_invoice_create(self):
        form = MonthlyInvoiceCreateForm(self.request.POST, prefix="invoice")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(invoice_form=form))
        issue_monthly_invoice(**form.cleaned_data)
        messages.success(self.request, "Fatura emitida.")
        return redirect("system:finance-dashboard")

    def _handle_pause_create(self):
        form = EnrollmentPauseCreateForm(self.request.POST, prefix="pause")
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(pause_form=form))
        create_enrollment_pause(**form.cleaned_data, actor_user=self.request.user)
        messages.success(self.request, "Trancamento registrado.")
        return redirect("system:finance-dashboard")

    def _invalid_action(self):
        messages.error(self.request, "Acao financeira invalida.")
        return redirect("system:finance-dashboard")


class InvoiceMarkPaidView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        mark_invoice_paid(self._get_invoice(), notes=request.POST.get("notes", ""), actor_user=request.user)
        messages.success(request, "Fatura marcada como paga.")
        return redirect("system:finance-dashboard")

    def _get_invoice(self):
        return get_object_or_404(get_invoices_queryset(), uuid=self.kwargs["uuid"])


class InvoiceMarkOverdueView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        mark_invoice_overdue(self._get_invoice(), notes=request.POST.get("notes", ""), actor_user=request.user)
        messages.success(request, "Fatura marcada como vencida.")
        return redirect("system:finance-dashboard")

    def _get_invoice(self):
        return get_object_or_404(get_invoices_queryset(), uuid=self.kwargs["uuid"])


class EnrollmentPauseResumeView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        resume_enrollment_pause(self._get_pause(), notes=request.POST.get("notes", ""), actor_user=request.user)
        messages.success(request, "Matricula retomada.")
        return redirect("system:finance-dashboard")

    def _get_pause(self):
        return get_object_or_404(get_pauses_queryset(), uuid=self.kwargs["uuid"])


class PaymentProofReviewView(RoleRequiredMixin, View):
    required_roles = ADMIN_ROLE_CODES

    def post(self, request, *args, **kwargs):
        form = PaymentProofReviewForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Nao foi possivel revisar o comprovante.")
            return redirect("system:finance-dashboard")
        review_payment_proof(
            proof=self._get_proof(),
            reviewer=request.user,
            approve=form.should_approve(),
            review_notes=form.cleaned_data["review_notes"],
        )
        messages.success(request, "Revisao de comprovante registrada.")
        return redirect("system:finance-dashboard")

    def _get_proof(self):
        return get_object_or_404(get_payment_proofs_queryset(), uuid=self.kwargs["uuid"])


class MyInvoicesView(LoginRequiredMixin, TemplateView):
    template_name = "system/finance/my_invoices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invoices"] = get_responsible_invoices_queryset(self.request.user)
        context["subscriptions"] = get_checkout_allowed_subscriptions(self.request.user).filter(
            responsible_user=self.request.user
        )
        context["proof_form"] = kwargs.get("proof_form") or PaymentProofUploadForm(user=self.request.user)
        context["stripe_is_configured"] = is_stripe_configured()
        return context

    def post(self, request, *args, **kwargs):
        form = PaymentProofUploadForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(proof_form=form))
        upload_payment_proof(
            invoice=form.get_invoice(),
            uploaded_by=request.user,
            uploaded_file=form.cleaned_data["uploaded_file"],
        )
        messages.success(request, "Comprovante enviado para analise.")
        return redirect("system:my-invoices")
