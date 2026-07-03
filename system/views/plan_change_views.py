from django.http import JsonResponse
from django.urls import reverse
from django.views import View

from system.constants import STUDENT_PORTAL_PERSON_TYPE_CODES
from system.models.plan import SubscriptionPlan
from system.services.membership import get_active_membership, get_membership_owner
from system.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    apply_plan_change_with_leftover_refund,
    calculate_plan_change,
    create_plan_change_order,
    get_plan_change_lock,
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

        raw_plan_id = (request.POST.get("selected_plan") or "").strip()
        try:
            plan_id = int(raw_plan_id)
        except (TypeError, ValueError):
            return JsonResponse(
                {"success": False, "error": "Selecione um plano antes de confirmar."},
                status=400,
            )

        new_plan = SubscriptionPlan.objects.filter(pk=plan_id, is_active=True).first()
        if new_plan is None:
            return JsonResponse(
                {"success": False, "error": "Plano selecionado não encontrado."}, status=404
            )

        if membership.plan_id == new_plan.pk:
            return JsonResponse(
                {"success": False, "error": "Plano selecionado é o mesmo que o atual."},
                status=400,
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
