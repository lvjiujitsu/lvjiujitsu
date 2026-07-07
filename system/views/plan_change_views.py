from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from system.constants import STUDENT_PORTAL_PERSON_TYPE_CODES
from system.models.membership import MembershipStatus
from system.services.membership import get_active_membership, get_membership_owner
from system.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    apply_plan_change_with_leftover_refund,
    calculate_plan_change,
    create_plan_change_order,
    create_plan_change_stripe_order,
    get_plan_change_lock,
    plan_requires_stripe_checkout,
)
from system.services.registration_checkout import resolve_catalog_plan
from system.services.stripe_checkout import (
    StripeCheckoutError,
    create_billing_portal_session,
    create_subscription_session_for_plan_change,
)
from system.views.portal_mixins import PortalRoleRequiredMixin


LEFTOVER_ACTION_KEEP = "keep_credit"
LEFTOVER_ACTION_REFUND = "refund"
VALID_LEFTOVER_ACTIONS = (LEFTOVER_ACTION_KEEP, LEFTOVER_ACTION_REFUND)


class PlanChangeSelectView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES

    def post(self, request):
        person = request.portal_person
        membership = get_active_membership(person)
        if not membership:
            return JsonResponse(
                {"success": False, "error": "Você não possui uma assinatura ativa."},
                status=400,
            )
        plan_change_lock = get_plan_change_lock(membership)
        if plan_change_lock["is_locked"]:
            return JsonResponse(
                {"success": False, "error": plan_change_lock["message"]},
                status=400,
            )

        catalog_id = (request.POST.get("selected_plan") or "").strip()
        if not catalog_id:
            return JsonResponse(
                {"success": False, "error": "Selecione um plano antes de confirmar."},
                status=400,
            )

        legacy_plan, plan_price = resolve_catalog_plan(catalog_id)
        new_plan = legacy_plan if legacy_plan is not None else plan_price
        if new_plan is None:
            return JsonResponse(
                {"success": False, "error": "Plano selecionado não encontrado."}, status=404
            )

        if plan_requires_stripe_checkout(new_plan):
            billing_owner = get_membership_owner(person) or person
            order = create_plan_change_stripe_order(billing_owner, membership, new_plan)
            try:
                session = create_subscription_session_for_plan_change(order, request)
            except StripeCheckoutError as exc:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)
            return JsonResponse({"success": True, "redirect_url": session["url"]})

        if membership.stripe_subscription_id:
            from system.services.stripe_admin_actions import (
                StripeAdminActionError,
                cancel_membership,
            )

            try:
                cancel_membership(
                    membership,
                    at_period_end=False,
                    reason="Migração para plano fora do Stripe.",
                )
            except StripeAdminActionError as exc:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)
            membership.status = MembershipStatus.ACTIVE
            membership.stripe_subscription_id = ""
            membership.canceled_at = None
            membership.cancel_at_period_end = False
            membership.save(
                update_fields=[
                    "status",
                    "stripe_subscription_id",
                    "canceled_at",
                    "cancel_at_period_end",
                    "updated_at",
                ]
            )

        leftover_action = (request.POST.get("leftover_action") or LEFTOVER_ACTION_KEEP).strip()
        if leftover_action not in VALID_LEFTOVER_ACTIONS:
            leftover_action = LEFTOVER_ACTION_KEEP

        try:
            proration = calculate_plan_change(membership, new_plan)
        except PlanChangeError as exc:
            return JsonResponse({"success": False, "error": str(exc)}, status=400)

        if proration["is_upgrade"]:
            billing_owner = get_membership_owner(person) or person
            order = create_plan_change_order(billing_owner, membership, new_plan, proration)
            return JsonResponse(
                {
                    "success": True,
                    "redirect_url": reverse("system:payment-checkout", kwargs={"order_id": order.pk}),
                }
            )

        if leftover_action == LEFTOVER_ACTION_REFUND and proration["has_leftover"]:
            try:
                apply_plan_change_with_leftover_refund(membership, new_plan, proration)
            except PlanChangeError as exc:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)
            return JsonResponse(
                {
                    "success": True,
                    "message": (
                        f"Plano alterado para {new_plan.display_name}. "
                        f"Sobra de R$ {proration['leftover_credit']} foi devolvida ao cliente."
                    ),
                }
            )

        apply_plan_change(None, membership, new_plan, proration=proration)
        if proration["has_leftover"]:
            message = (
                f"Plano alterado para {new_plan.display_name}. "
                f"Sobra de R$ {proration['leftover_credit']} ficou como crédito "
                f"para a próxima renovação."
            )
        else:
            message = f"Plano alterado para {new_plan.display_name}."
        return JsonResponse({"success": True, "message": message})


class MembershipUpdateCardView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES

    def get(self, request):
        person = request.portal_person
        membership = get_active_membership(person)
        if not membership or not membership.is_stripe_recurring:
            messages.error(request, "Nenhuma assinatura recorrente Stripe encontrada.")
            return redirect("system:home")

        try:
            session = create_billing_portal_session(membership, request)
        except StripeCheckoutError as exc:
            messages.error(request, str(exc))
            return redirect("system:home")

        from system.models.membership_timeline import MembershipTimelineEventType
        from system.services.membership_timeline import record_membership_event

        record_membership_event(
            person,
            MembershipTimelineEventType.CARD_UPDATED,
            membership=membership,
            actor=person,
        )
        return redirect(session["url"])
