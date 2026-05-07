from collections import OrderedDict

from django.contrib import messages
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from system.models.membership import MembershipStatus
from system.models.plan import (
    BillingCycle,
    SubscriptionPlan,
)
from system.constants import STUDENT_PORTAL_PERSON_TYPE_CODES
from system.selectors.plan_eligibility import (
    build_eligibility_context_for_person,
    get_eligible_plans,
)
from system.services.membership import get_active_membership, get_membership_owner
from system.services.plan_change import (
    PlanChangeError,
    apply_plan_change,
    calculate_plan_change,
    create_plan_change_order,
)
from system.views.portal_mixins import PortalRoleRequiredMixin


CYCLE_DISPLAY_ORDER = {
    BillingCycle.MONTHLY: 0,
    BillingCycle.QUARTERLY: 1,
    BillingCycle.SEMIANNUAL: 2,
    BillingCycle.ANNUAL: 3,
}


class PlanChangeSelectView(PortalRoleRequiredMixin, TemplateView):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES
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
            billing_owner = get_membership_owner(person) or person
            eligibility = build_eligibility_context_for_person(billing_owner)
            available_plans = get_eligible_plans(eligibility).exclude(pk=membership.plan_id)
            plans_with_proration = []
            for plan in available_plans:
                try:
                    proration = calculate_plan_change(membership, plan)
                    plans_with_proration.append({"plan": plan, "proration": proration})
                except PlanChangeError:
                    continue
            context["plans_with_proration"] = plans_with_proration
            context["plan_groups"] = _group_plans_by_audience_and_frequency(plans_with_proration)
        else:
            context["plans_with_proration"] = []
            context["plan_groups"] = []

        context["back_url"] = reverse("system:student-home")

        return context


def _group_plans_by_audience_and_frequency(plans_with_proration):
    groups = OrderedDict([
        (False, {"label": "Planos Individuais", "entries": []}),
        (True, {"label": "Planos Família", "entries": []}),
    ])
    for entry in plans_with_proration:
        plan = entry["plan"]
        groups[plan.is_family_plan]["entries"].append(entry)
    for group in groups.values():
        group["entries"].sort(
            key=lambda item: (
                CYCLE_DISPLAY_ORDER.get(item["plan"].billing_cycle, 99),
                item["plan"].price,
            )
        )
    return [group for group in groups.values() if group["entries"]]


class PlanChangeConfirmView(PortalRoleRequiredMixin, View):
    allowed_codes = STUDENT_PORTAL_PERSON_TYPE_CODES

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
