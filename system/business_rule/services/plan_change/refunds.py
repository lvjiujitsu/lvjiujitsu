from django.db import transaction
from django.utils import timezone
from system.business_rule.models.membership import (
    MembershipCredit,
    MembershipCreditSource,
    MembershipCreditStatus,
)
from system.business_rule.models.registration_order import PaymentProvider
from system.business_rule.services.asaas_client import AsaasClientError, refund_payment
from system.business_rule.services.payroll_rules import append_order_refund_record
from system.business_rule.services.stripe_admin_actions import StripeAdminActionError, refund_order
from system.business_rule.services.plan_change.application import apply_plan_change
from system.business_rule.services.plan_change.primitives import PlanChangeError, current_plan_reference
from system.business_rule.services.plan_change.queries import get_last_paid_order_for_plan


@transaction.atomic
def refund_plan_change_leftover(membership, amount, *, source_order=None, current_plan=None):
    plan_for_lookup = current_plan or current_plan_reference(membership)
    last_order = source_order or get_last_paid_order_for_plan(
        membership.person, plan_for_lookup
    )
    if last_order is None:
        raise PlanChangeError(
            "Nenhuma cobrança paga encontrada para devolver o valor."
        )

    provider = last_order.payment_provider
    refund_reference = ""

    if provider == PaymentProvider.STRIPE:
        if not last_order.stripe_payment_intent_id:
            raise PlanChangeError(
                "Pedido Stripe sem PaymentIntent — não é possível estornar."
            )
        try:
            result = refund_order(
                last_order,
                amount=amount,
                reason="Sobra de troca de plano",
            )
        except StripeAdminActionError as exc:
            raise PlanChangeError(f"Falha no estorno Stripe: {exc}") from exc
        refund_reference = str(result.get("refund_id") or "")
    elif provider == PaymentProvider.ASAAS:
        if not last_order.asaas_payment_id:
            raise PlanChangeError(
                "Pedido Asaas sem ID de pagamento — não é possível estornar."
            )
        try:
            result = refund_payment(
                last_order.asaas_payment_id,
                value=amount,
                description="Sobra de troca de plano",
            )
        except AsaasClientError as exc:
            raise PlanChangeError(f"Falha no estorno Asaas: {exc}") from exc
        refund_reference = str(result.get("id") or "")
        last_order.refunded_at = timezone.now()
        append_order_refund_record(
            last_order,
            amount,
            source="asaas_plan_change_refund",
            cumulative=True,
            reason="Sobra de troca de plano",
            save=False,
        )
        last_order.save(
            update_fields=["refunded_at", "notes", "updated_at"]
        )
    else:
        raise PlanChangeError(
            "Pagamento original não suporta devolução automática."
        )

    credit = MembershipCredit.objects.create(
        membership=membership,
        amount=amount,
        source=MembershipCreditSource.PLAN_CHANGE_LEFTOVER,
        status=MembershipCreditStatus.REFUNDED,
        source_order=last_order,
        refund_provider=provider or "",
        refund_provider_reference=refund_reference,
        refunded_at=timezone.now(),
        notes="Sobra de troca de plano devolvida ao cliente.",
    )
    return credit


@transaction.atomic
def apply_plan_change_with_leftover_refund(
    membership, new_plan, proration, *, source_order=None
):
    current_plan = membership.plan
    membership = apply_plan_change(
        None, membership, new_plan, proration=proration
    )
    leftover = proration["leftover_credit"]
    if leftover <= 0:
        return membership, None

    available_credit = (
        MembershipCredit.objects.filter(
            membership=membership,
            status=MembershipCreditStatus.AVAILABLE,
            source=MembershipCreditSource.PLAN_CHANGE_LEFTOVER,
        )
        .order_by("-created_at")
        .first()
    )

    refund = refund_plan_change_leftover(
        membership,
        leftover,
        source_order=source_order,
        current_plan=current_plan,
    )

    if available_credit is not None:
        available_credit.status = MembershipCreditStatus.REFUNDED
        available_credit.refund_provider = refund.refund_provider
        available_credit.refund_provider_reference = refund.refund_provider_reference
        available_credit.refunded_at = refund.refunded_at
        available_credit.notes = (
            (available_credit.notes or "")
            + " | Convertido em devolução automática."
        ).strip()
        available_credit.save(
            update_fields=[
                "status",
                "refund_provider",
                "refund_provider_reference",
                "refunded_at",
                "notes",
                "updated_at",
            ]
        )
        refund.delete()
        return membership, available_credit
    return membership, refund
