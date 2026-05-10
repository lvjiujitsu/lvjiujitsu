from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from system.constants import STUDENT_PORTAL_PERSON_TYPE_CODES
from system.models.membership import MembershipStatus
from system.models.plan import SubscriptionPlan
from system.selectors.plan_eligibility import (
    build_eligibility_context_for_person,
    get_eligible_plans,
)
from system.services.membership import get_active_membership, get_membership_owner
from system.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    apply_plan_change_with_leftover_refund,
    calculate_plan_change,
    create_plan_change_order,
    get_last_paid_order,
)
from system.views.portal_mixins import PortalRoleRequiredMixin


_CYCLE_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}

LEFTOVER_ACTION_KEEP = "keep_credit"
LEFTOVER_ACTION_REFUND = "refund"
VALID_LEFTOVER_ACTIONS = (LEFTOVER_ACTION_KEEP, LEFTOVER_ACTION_REFUND)


def _build_installment_label(plan):
    if plan.payment_method != "credit_card":
        return ""
    n = _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan.monthly_reference_price:
        price_str = f"R$ {plan.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"


def _serialize_plan_with_proration(plan, proration):
    return {
        "id": plan.pk,
        "code": plan.code,
        "name": plan.display_name,
        "price": str(plan.price),
        "monthly_reference_price": (
            str(plan.monthly_reference_price)
            if plan.monthly_reference_price is not None
            else ""
        ),
        "cycle": plan.get_billing_cycle_display(),
        "billing_cycle": plan.billing_cycle,
        "payment_method": plan.payment_method,
        "payment_method_label": plan.get_payment_method_display(),
        "is_family_plan": plan.is_family_plan,
        "audience": plan.audience,
        "audience_label": plan.get_audience_display(),
        "weekly_frequency": plan.weekly_frequency,
        "weekly_frequency_label": plan.get_weekly_frequency_display(),
        "installment_label": _build_installment_label(plan),
        "installment_count": (
            _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
            if plan.payment_method == "credit_card"
            else 0
        ),
        "proration": {
            "cycles_covered": proration["cycles_covered"],
            "extension_months": proration["extension_months"],
            "new_period_end": proration["new_period_end"].isoformat(),
            "leftover_credit": str(proration["leftover_credit"]),
            "additional_charge": str(proration["additional_charge"]),
            "is_upgrade": proration["is_upgrade"],
            "is_extension": proration["is_extension"],
            "has_leftover": proration["has_leftover"],
        },
    }


def _build_membership_summary(person, membership):
    if membership is None:
        return None
    last_order = get_last_paid_order(membership)
    amount_paid = (
        Decimal(last_order.total) if last_order and last_order.total
        else Decimal(membership.plan.price or 0)
    )
    period_start = membership.current_period_start
    period_end = membership.current_period_end
    cycle_days = max((period_end - period_start).days, 1) if period_start and period_end else 0
    now = timezone.now()
    days_used = max(0, min((now - period_start).days, cycle_days)) if period_start else 0
    days_remaining = max(0, cycle_days - days_used)

    if amount_paid > 0 and cycle_days > 0:
        daily = amount_paid / Decimal(cycle_days)
        consumed = (daily * Decimal(days_used)).quantize(Decimal("0.01"))
        available = (amount_paid - consumed).quantize(Decimal("0.01"))
    else:
        consumed = Decimal("0.00")
        available = Decimal("0.00")
    if available < 0:
        available = Decimal("0.00")

    return {
        "plan_name": membership.plan.display_name,
        "plan_cycle": membership.plan.get_billing_cycle_display(),
        "amount_paid": str(amount_paid.quantize(Decimal("0.01"))),
        "amount_consumed": str(consumed),
        "available_credit": str(available),
        "cycle_days": cycle_days,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "period_end": period_end.isoformat() if period_end else "",
        "payment_provider": last_order.payment_provider if last_order else "",
        "refund_supported": bool(
            last_order
            and last_order.payment_provider in ("stripe", "asaas")
            and (last_order.stripe_payment_intent_id or last_order.asaas_payment_id)
        ),
    }


def _build_plan_catalog(person, membership):
    if not membership or membership.status not in (
        MembershipStatus.ACTIVE,
        MembershipStatus.EXEMPTED,
    ):
        return []
    billing_owner = get_membership_owner(person) or person
    eligibility = build_eligibility_context_for_person(billing_owner)
    available_plans = get_eligible_plans(eligibility).exclude(pk=membership.plan_id)
    catalog = []
    for plan in available_plans:
        try:
            proration = calculate_plan_change(membership, plan)
        except PlanChangeError:
            continue
        catalog.append(_serialize_plan_with_proration(plan, proration))
    return catalog


class PlanChangeSelectView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES
    template_name = "billing/plan_change_select.html"

    def get(self, request):
        person = request.portal_person
        membership = get_active_membership(person)
        catalog = _build_plan_catalog(person, membership)
        context = {
            "membership": membership,
            "membership_summary": _build_membership_summary(person, membership),
            "plan_catalog": catalog,
            "back_url": reverse("system:student-home"),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        person = request.portal_person
        membership = get_active_membership(person)
        if not membership:
            messages.error(request, "Você não possui uma assinatura ativa.")
            return redirect("system:student-home")

        raw_plan_id = (request.POST.get("selected_plan") or "").strip()
        if not raw_plan_id:
            messages.error(request, "Selecione um plano antes de confirmar.")
            return redirect("system:plan-change-select")

        try:
            plan_id = int(raw_plan_id)
        except (TypeError, ValueError):
            messages.error(request, "Selecione um plano antes de confirmar.")
            return redirect("system:plan-change-select")

        new_plan = get_object_or_404(SubscriptionPlan, pk=plan_id, is_active=True)

        if membership.plan_id == new_plan.pk:
            messages.error(request, "Plano selecionado é o mesmo que o atual.")
            return redirect("system:plan-change-select")

        leftover_action = (request.POST.get("leftover_action") or LEFTOVER_ACTION_KEEP).strip()
        if leftover_action not in VALID_LEFTOVER_ACTIONS:
            leftover_action = LEFTOVER_ACTION_KEEP

        try:
            proration = calculate_plan_change(membership, new_plan)
        except PlanChangeError as exc:
            messages.error(request, str(exc))
            return redirect("system:plan-change-select")

        if proration["is_upgrade"]:
            billing_owner = get_membership_owner(person) or person
            order = create_plan_change_order(
                billing_owner, membership, new_plan, proration
            )
            return redirect("system:payment-checkout", order_id=order.pk)

        if leftover_action == LEFTOVER_ACTION_REFUND and proration["has_leftover"]:
            try:
                apply_plan_change_with_leftover_refund(
                    membership, new_plan, proration
                )
            except PlanChangeError as exc:
                messages.error(request, str(exc))
                return redirect("system:plan-change-select")
            messages.success(
                request,
                f"Plano alterado para {new_plan.display_name}. "
                f"Sobra de R$ {proration['leftover_credit']} foi devolvida ao cliente.",
            )
            return redirect("system:student-home")

        apply_plan_change(None, membership, new_plan, proration=proration)
        if proration["has_leftover"]:
            messages.success(
                request,
                f"Plano alterado para {new_plan.display_name}. "
                f"Sobra de R$ {proration['leftover_credit']} ficou como crédito "
                f"para a próxima renovação.",
            )
        else:
            messages.success(
                request, f"Plano alterado para {new_plan.display_name}."
            )
        return redirect("system:student-home")
