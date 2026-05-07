import json
import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from system.models.asaas import (
    PayoutStatus,
    TeacherBankAccount,
    TeacherPayout,
    TeacherPayrollConfig,
)
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.constants import (
    ADMINISTRATIVE_PERSON_TYPE_CODES,
    INSTRUCTOR_PERSON_TYPE_CODES,
)
from system.services.asaas_checkout import (
    AsaasCheckoutError,
    create_pix_charge_for_order,
)
from system.services.asaas_client import verify_webhook_token
from system.services.asaas_payroll import (
    PayrollError,
    approve_payout,
    compute_available_balance,
    dispatch_payout,
    refuse_payout,
    request_withdrawal,
)
from system.services.asaas_webhooks import process_asaas_event
from system.services.payroll_rules import (
    calculate_monthly_payroll,
    get_staff_financial_context,
)
from system.views.portal_mixins import (
    PortalLoginRequiredMixin,
    PortalRoleRequiredMixin,
)


logger = logging.getLogger(__name__)


class CreatePixChargeView(View):
    def post(self, request, order_id, *args, **kwargs):
        return self._start(request, order_id)

    def get(self, request, order_id, *args, **kwargs):
        return self._start(request, order_id)

    def _start(self, request, order_id):
        try:
            order = RegistrationOrder.objects.select_related("plan", "person").get(
                pk=order_id
            )
        except RegistrationOrder.DoesNotExist:
            messages.error(request, "Pedido não encontrado.")
            return redirect("system:root")

        if not self._is_authorized(request, order):
            messages.error(request, "Pedido não encontrado.")
            return redirect("system:root")

        if order.payment_status in (
            PaymentStatus.PAID,
            PaymentStatus.EXEMPTED,
            PaymentStatus.REFUNDED,
        ):
            messages.info(request, "Este pedido já foi processado.")
            return redirect("system:dashboard-redirect")

        try:
            pix = create_pix_charge_for_order(order)
        except AsaasCheckoutError as exc:
            logger.error("Falha PIX Asaas: %s", exc)
            messages.error(
                request,
                "Pagamento PIX indisponível no momento. "
                "Tente cartão ou conclua e pague depois.",
            )
            return redirect("system:payment-checkout", order_id=order.pk)
        except Exception:
            logger.exception("Erro inesperado no PIX Asaas")
            messages.error(
                request,
                "Pagamento PIX indisponível no momento. "
                "Tente cartão ou conclua e pague depois.",
            )
            return redirect("system:payment-checkout", order_id=order.pk)

        return render(
            request,
            "billing/pix_checkout.html",
            {"order": order, "pix": pix},
        )

    def _is_authorized(self, request, order):
        person = order.person
        portal_person = getattr(request, "portal_person", None)
        if portal_person and portal_person.pk == person.pk:
            return True
        if getattr(request, "portal_is_technical_admin", False):
            return True
        session_order_id = request.session.get("pending_checkout_order_id")
        if session_order_id and int(session_order_id) == order.pk:
            return True
        return False


@method_decorator(csrf_exempt, name="dispatch")
class AsaasWebhookView(View):
    def post(self, request, *args, **kwargs):
        received_token = request.META.get("HTTP_ASAAS_ACCESS_TOKEN", "")
        try:
            ok = verify_webhook_token(received_token)
        except Exception:
            logger.exception("Webhook Asaas mal configurado")
            return HttpResponse(status=500)
        if not ok:
            return HttpResponse(status=401)
        try:
            event = json.loads(request.body or b"{}")
        except ValueError:
            return HttpResponse(status=400)
        try:
            result = process_asaas_event(event)
        except Exception:
            logger.exception("Falha ao processar evento Asaas %s", event.get("id"))
            return HttpResponse(status=500)
        logger.info(
            "Asaas event processed: id=%s type=%s order=%s payout=%s duplicate=%s",
            event.get("id"),
            event.get("event"),
            getattr(result["order"], "pk", None),
            getattr(result["payout"], "pk", None),
            result["duplicate"],
        )
        return HttpResponse(status=200)


class AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES


class PayrollListView(AdministrativeRequiredMixin, ListView):
    template_name = "billing/payroll_list.html"
    context_object_name = "configs"
    paginate_by = 30

    def get_queryset(self):
        return (
            TeacherPayrollConfig.objects.select_related("person")
            .order_by("person__full_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for config in context["configs"]:
            config.current_calculation = calculate_monthly_payroll(config.person)
        context["bank_accounts"] = {
            ba.person_id: ba
            for ba in TeacherBankAccount.objects.filter(
                person_id__in=[c.person_id for c in context["configs"]]
            )
        }
        return context


class PayoutQueueView(AdministrativeRequiredMixin, ListView):
    template_name = "billing/payout_queue.html"
    context_object_name = "payouts"
    paginate_by = 30

    def get_queryset(self):
        qs = TeacherPayout.objects.select_related("person", "bank_account").order_by(
            "-created_at"
        )
        status = self.request.GET.get("status") or ""
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status") or ""
        context["status_choices"] = PayoutStatus.choices
        return context


class PayoutApproveView(AdministrativeRequiredMixin, View):
    success_url = reverse_lazy("system:payout-queue")

    def post(self, request, payout_id, *args, **kwargs):
        payout = get_object_or_404(TeacherPayout, pk=payout_id)
        notes = request.POST.get("notes", "")
        admin_user = getattr(request, "user", None)
        try:
            approve_payout(payout, admin_user=admin_user, notes=notes)
            messages.success(request, "Pagamento aprovado.")
        except PayrollError as exc:
            messages.error(request, str(exc))
        return redirect(request.POST.get("next") or self.success_url)


class PayoutRefuseView(AdministrativeRequiredMixin, View):
    success_url = reverse_lazy("system:payout-queue")

    def post(self, request, payout_id, *args, **kwargs):
        payout = get_object_or_404(TeacherPayout, pk=payout_id)
        notes = request.POST.get("notes", "")
        admin_user = getattr(request, "user", None)
        try:
            refuse_payout(payout, admin_user=admin_user, notes=notes)
            messages.success(request, "Pagamento recusado.")
        except PayrollError as exc:
            messages.error(request, str(exc))
        return redirect(request.POST.get("next") or self.success_url)


class StaffFinancialRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = INSTRUCTOR_PERSON_TYPE_CODES + ADMINISTRATIVE_PERSON_TYPE_CODES


class TeacherFinancialView(StaffFinancialRequiredMixin, View):
    template_name = "home/instructor/financial.html"

    def get(self, request, *args, **kwargs):
        from system.forms import WithdrawalRequestForm

        context = self._build_context(request, form=WithdrawalRequestForm())
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        from system.forms import WithdrawalRequestForm

        form = WithdrawalRequestForm(request.POST)
        if not form.is_valid():
            context = self._build_context(request, form=form)
            return render(request, self.template_name, context)

        person = request.portal_person
        try:
            request_withdrawal(
                person,
                form.cleaned_data["amount"],
                notes=form.cleaned_data.get("notes", ""),
            )
        except PayrollError as exc:
            form.add_error("amount", str(exc))
            context = self._build_context(request, form=form)
            return render(request, self.template_name, context)

        messages.success(
            request,
            "Solicitação enviada. Aguarde aprovação administrativa.",
        )
        return redirect("system:teacher-financial")

    def _build_context(self, request, *, form):
        person = request.portal_person
        staff_context = get_staff_financial_context(person)
        available, base, committed = compute_available_balance(person)
        recent_payouts = list(
            TeacherPayout.objects.filter(person=person)
            .order_by("-reference_month", "-created_at")[:10]
        )
        try:
            config = person.payroll_config
        except TeacherPayrollConfig.DoesNotExist:
            config = None
        try:
            bank = person.teacher_bank_account
        except TeacherBankAccount.DoesNotExist:
            bank = None
        return {
            "form": form,
            "config": config,
            "bank": bank,
            "available_balance": available,
            "base_salary": base,
            "committed_total": committed,
            "recent_payouts": recent_payouts,
            "calculation": staff_context["calculation"],
            "linked_entries": staff_context["linked_entries"],
        }


class PayoutDispatchView(AdministrativeRequiredMixin, View):
    success_url = reverse_lazy("system:payout-queue")

    def post(self, request, payout_id, *args, **kwargs):
        payout = get_object_or_404(TeacherPayout, pk=payout_id)
        try:
            dispatch_payout(payout)
            messages.success(request, "Pagamento enviado ao Asaas.")
        except PayrollError as exc:
            messages.error(request, f"Falha: {exc}")
        return redirect(request.POST.get("next") or self.success_url)
