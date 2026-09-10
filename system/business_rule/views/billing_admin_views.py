from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from system.core.http import safe_redirect_target
from system.business_rule.models.membership import Membership
from system.business_rule.models.plan import SubscriptionPlan
from system.business_rule.models.registration_order import (
    PaymentStatus,
    RegistrationOrder,
)
from system.business_rule.constants import ADMINISTRATIVE_PERSON_TYPE_CODES
from system.business_rule.constants import AuditModule, ProductAuditAction
from system.core.audit import record_event
from system.business_rule.services.membership import (
    exempt_order,
    mark_order_manually_paid,
)
from system.business_rule.services.stripe_admin_actions import (
    StripeAdminActionError,
    cancel_membership,
    change_membership_plan,
    refund_order,
)
from system.business_rule.services.financial_dashboard import build_financial_dashboard
from system.business_rule.access import PortalRoleRequiredMixin
from system.business_rule.services.portal_auth import (
    resolve_technical_admin_from_session,
)


class _BillingAdminMixin(PortalRoleRequiredMixin):
    allowed_codes = ADMINISTRATIVE_PERSON_TYPE_CODES

    def _resolve_admin_user(self, request):
        return resolve_technical_admin_from_session(request)


class ApprovalQueueView(_BillingAdminMixin, ListView):
    template_name = "business_rule/billing/approval_queue.html"
    context_object_name = "orders"
    paginate_by = 30

    def get_queryset(self):
        return (
            RegistrationOrder.objects.filter(
                payment_status=PaymentStatus.PENDING,
                total=0,
            )
            .select_related("person", "plan")
            .order_by("-created_at")
        )


class PendingPaymentListView(_BillingAdminMixin, ListView):
    template_name = "business_rule/billing/pending_payments.html"
    context_object_name = "orders"
    paginate_by = 30

    def get_queryset(self):
        return (
            RegistrationOrder.objects.filter(total__gt=0)
            .exclude(
                payment_status__in=(
                    PaymentStatus.PAID,
                    PaymentStatus.EXEMPTED,
                    PaymentStatus.REFUNDED,
                )
            )
            .select_related("person", "plan")
            .order_by("-created_at")
        )


class FinancialControlView(_BillingAdminMixin, ListView):
    template_name = "business_rule/billing/financial_entries.html"
    context_object_name = "orders"
    paginate_by = 50

    def get_queryset(self):
        return (
            RegistrationOrder.objects.filter(total__gt=0)
            .select_related("person", "plan")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["financial_dashboard"] = build_financial_dashboard()
        return context


class ExemptOrderActionView(_BillingAdminMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(RegistrationOrder, pk=order_id)
        notes = request.POST.get("notes", "").strip()
        admin_user = self._resolve_admin_user(request)
        exempt_order(order, admin_user, notes=notes)
        messages.success(
            request, f"Pedido #{order.pk} isento com sucesso."
        )
        return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:approval-queue")
                )
            )


class MarkOrderPaidActionView(_BillingAdminMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(RegistrationOrder, pk=order_id)
        notes = request.POST.get("notes", "").strip()
        admin_user = self._resolve_admin_user(request)
        mark_order_manually_paid(order, admin_user, notes=notes)
        record_event(
            request,
            ProductAuditAction.MARK_PAID,
            AuditModule.FINANCIAL,
            f"Pedido #{order.pk} · {order.person.full_name}",
            f"Marcado como pago manualmente. R$ {order.total}.",
        )
        messages.success(
            request, f"Pedido #{order.pk} marcado como pago."
        )
        return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )


class RefundOrderActionView(_BillingAdminMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(RegistrationOrder, pk=order_id)
        raw_amount = request.POST.get("amount", "").strip()
        reason = request.POST.get("reason", "").strip()
        amount = None
        if raw_amount:
            try:
                amount = Decimal(raw_amount.replace(",", "."))
            except InvalidOperation:
                messages.error(request, "Valor de reembolso inválido.")
                return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )
        try:
            result = refund_order(
                order,
                amount=amount,
                admin_user=self._resolve_admin_user(request),
                reason=reason,
            )
        except StripeAdminActionError as exc:
            messages.error(request, f"Falha ao estornar: {exc}")
            return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )
        messages.success(
            request,
            f"Estorno R$ {result['amount']} realizado para pedido #{order.pk}.",
        )
        return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )


class CancelMembershipActionView(_BillingAdminMixin, View):
    def post(self, request, membership_id):
        membership = get_object_or_404(Membership, pk=membership_id)
        at_period_end = request.POST.get("at_period_end", "1") == "1"
        reason = request.POST.get("reason", "").strip()
        try:
            cancel_membership(
                membership,
                at_period_end=at_period_end,
                admin_user=self._resolve_admin_user(request),
                reason=reason,
            )
        except StripeAdminActionError as exc:
            messages.error(request, f"Falha ao cancelar assinatura: {exc}")
            return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )
        kind = "fim do período" if at_period_end else "imediata"
        messages.success(
            request, f"Assinatura #{membership.pk} cancelada ({kind})."
        )
        return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )


class ChangeMembershipPlanActionView(_BillingAdminMixin, View):
    def post(self, request, membership_id):
        membership = get_object_or_404(Membership, pk=membership_id)
        new_plan_id = request.POST.get("plan_id")
        new_plan = get_object_or_404(SubscriptionPlan, pk=new_plan_id, is_active=True)
        try:
            change_membership_plan(
                membership,
                new_plan,
                admin_user=self._resolve_admin_user(request),
            )
        except StripeAdminActionError as exc:
            messages.error(request, f"Falha ao trocar plano: {exc}")
            return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )
        messages.success(
            request, f"Plano da assinatura #{membership.pk} alterado para {new_plan.display_name}."
        )
        return redirect(
                safe_redirect_target(
                    request, request.POST.get("next"), fallback=reverse("system:pending-payments")
                )
            )
