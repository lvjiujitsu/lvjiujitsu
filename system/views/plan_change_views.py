from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from system.models.membership import MembershipStatus
from system.models.plan import SubscriptionPlan
from system.services.membership import get_active_membership, get_membership_owner
from system.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    calculate_plan_change,
    create_plan_change_order,
)
from system.views.portal_mixins import PortalRoleRequiredMixin


class PlanChangeSelectView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = ("student", "guardian", "dependent")
    template_name = "billing/plan_change_select.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.request.portal_person
        membership = get_active_membership(person)
        context["membership"] = membership

        if membership and membership.status in (
            MembershipStatus.ACTIVE,
            MembershipStatus.EXEMPTED,
        ):
            available_plans = SubscriptionPlan.objects.filter(is_active=True).exclude(
                pk=membership.plan_id
            )
            plans_with_proration = []
            for plan in available_plans:
                try:
                    proration = calculate_plan_change(membership, plan)
                    plans_with_proration.append({"plan": plan, "proration": proration})
                except PlanChangeError:
                    continue
            context["plans_with_proration"] = plans_with_proration
        else:
            context["plans_with_proration"] = []

        return context


class PlanChangeConfirmView(PortalRoleRequiredMixin, View):
    allowed_codes = ("student", "guardian", "dependent")

    def get(self, request, plan_id):
        person = request.portal_person
        membership = get_active_membership(person)
        new_plan = get_object_or_404(SubscriptionPlan, pk=plan_id, is_active=True)

        if not membership or membership.plan_id == new_plan.pk:
            messages.error(request, "Troca de plano inválida.")
            return redirect("system:student-home")

        try:
            proration = calculate_plan_change(membership, new_plan)
        except PlanChangeError as e:
            messages.error(request, str(e))
            return redirect("system:plan-change-select")

        return render(
            request,
            "billing/plan_change_confirm.html",
            {
                "membership": membership,
                "new_plan": new_plan,
                "proration": proration,
            },
        )

    def post(self, request, plan_id):
        person = request.portal_person
        membership = get_active_membership(person)
        new_plan = get_object_or_404(SubscriptionPlan, pk=plan_id, is_active=True)

        if not membership or membership.plan_id == new_plan.pk:
            messages.error(request, "Troca de plano inválida.")
            return redirect("system:student-home")

        try:
            proration = calculate_plan_change(membership, new_plan)
        except PlanChangeError as e:
            messages.error(request, str(e))
            return redirect("system:plan-change-select")

        if proration["net_amount"] <= 0:
            apply_plan_change(None, membership, new_plan)
            messages.success(
                request, f"Plano alterado para {new_plan.display_name}."
            )
            return redirect("system:student-home")

        billing_owner = get_membership_owner(person)
        order = create_plan_change_order(
            billing_owner, membership, new_plan, proration
        )
        return redirect("system:payment-checkout", order_id=order.pk)
