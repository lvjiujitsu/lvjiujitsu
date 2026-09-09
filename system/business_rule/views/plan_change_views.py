from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from system.business_rule.constants import STUDENT_PORTAL_PERSON_TYPE_CODES
from system.business_rule.services.membership import get_active_membership, get_membership_owner
from system.business_rule.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    apply_plan_change_with_leftover_refund,
    calculate_plan_change,
    create_plan_change_order,
    create_plan_change_stripe_order,
    get_plan_change_lock,
    migrate_membership_off_stripe,
    plan_requires_stripe_checkout,
)
from system.business_rule.services.registration_checkout import resolve_catalog_plan
from system.business_rule.services.stripe_checkout import (
    StripeCheckoutError,
    create_billing_portal_session,
    create_subscription_session_for_plan_change,
    get_membership_default_payment_method_id,
)
from system.business_rule.access import PortalRoleRequiredMixin, portal_person
from system.business_rule.services.stripe_admin_actions import StripeAdminActionError
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.models.membership_timeline import MembershipTimelineEventType


LEFTOVER_ACTION_KEEP = "keep_credit"
LEFTOVER_ACTION_REFUND = "refund"
VALID_LEFTOVER_ACTIONS = (LEFTOVER_ACTION_KEEP, LEFTOVER_ACTION_REFUND)
CARD_UPDATE_SESSION_KEY = "pending_card_update"


class PlanChangeSelectView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES

    def post(self, request):
        person = portal_person(request)
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

            try:
                migrate_membership_off_stripe(membership)
            except StripeAdminActionError as exc:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)

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
        person = portal_person(request)
        membership = get_active_membership(person)
        if not membership or not membership.is_stripe_recurring:
            messages.error(request, "Nenhuma assinatura recorrente Stripe encontrada.")
            return redirect("system:home")

        if request.GET.get("card_update") == "confirm":
            return self._confirm_update(request, person, membership)

        try:
            previous_payment_method_id = get_membership_default_payment_method_id(
                membership
            )
            session = create_billing_portal_session(membership, request)
        except StripeCheckoutError as exc:
            messages.error(request, str(exc))
            return redirect("system:home")

        request.session[CARD_UPDATE_SESSION_KEY] = {
            "membership_id": membership.pk,
            "previous_payment_method_id": previous_payment_method_id,
        }
        return redirect(session["url"])

    def _confirm_update(self, request, person, membership):
        pending_update = request.session.pop(CARD_UPDATE_SESSION_KEY, None)
        if not pending_update or pending_update.get("membership_id") != membership.pk:
            messages.error(request, "Não foi possível validar a troca do cartão.")
            return redirect("system:home")

        try:
            payment_method_id = get_membership_default_payment_method_id(membership)
        except StripeCheckoutError as exc:
            messages.error(request, str(exc))
            return redirect("system:home")

        previous_payment_method_id = pending_update.get(
            "previous_payment_method_id"
        ) or ""
        if not payment_method_id or payment_method_id == previous_payment_method_id:
            messages.info(request, "Nenhuma alteração de cartão foi identificada.")
            return redirect("system:home")


        record_membership_event(
            person,
            MembershipTimelineEventType.CARD_UPDATED,
            membership=membership,
            actor=person,
            context={
                "previous_payment_method_id": previous_payment_method_id,
                "payment_method_id": payment_method_id,
            },
        )
        messages.success(request, "Cartão atualizado com sucesso.")
        return redirect("system:home")
