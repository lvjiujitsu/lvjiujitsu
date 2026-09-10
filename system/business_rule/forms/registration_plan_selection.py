from system.business_rule.constants import CheckoutAction
from system.business_rule.selectors.plan_eligibility import (
    build_eligibility_context_for_registration,
    is_plan_eligible,
)
from system.business_rule.services.registration_checkout import (
    parse_selected_products,
    resolve_catalog_plan,
    resolve_selected_product_items,
)
from system.business_rule.services.financial_transactions import resolve_checkout_action_for_plan
from system.business_rule.models.plan import PlanAudience


class RegistrationPlanSelectionMixin:
    def _clean_plan_selection(self, profile, include_dependent, extra_dependents):
        catalog_id = self.cleaned_data.get("selected_plan")
        if not catalog_id:
            return
        legacy_plan, plan_price = resolve_catalog_plan(catalog_id)
        if legacy_plan is None and plan_price is None:
            self.add_error("selected_plan", "Selecione um plano válido.")
            return

        context = build_eligibility_context_for_registration(self.cleaned_data)

        if legacy_plan is not None:
            if not is_plan_eligible(legacy_plan, context):
                self.add_error(
                    "selected_plan",
                    self._build_plan_ineligible_message(legacy_plan, context),
                )
                return
            resolved_plan = legacy_plan
        else:

            if plan_price.audience == PlanAudience.ADULT and not context.adult_active:
                self.add_error("selected_plan", "Plano Adulto exige aluno adulto cadastrado.")
                return
            if (
                plan_price.audience == PlanAudience.KIDS_JUVENILE
                and context.kids_juvenile_active_count < 1
            ):
                self.add_error("selected_plan", "Plano Kids/Juvenil exige aluno menor cadastrado.")
                return
            resolved_plan = plan_price

        checkout_action = self.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
        expected_action = resolve_checkout_action_for_plan(resolved_plan)
        if checkout_action != CheckoutAction.PAY_LATER and checkout_action != expected_action:
            self.add_error(
                "checkout_action",
                "O meio de pagamento escolhido não corresponde ao plano selecionado.",
            )

    def _build_plan_ineligible_message(self, plan, context):
        if plan.requires_special_authorization:
            return "Este plano exige autorização especial da academia."
        if plan.is_family_plan:
            return (
                "Plano familiar disponível apenas quando há ao menos dois alunos "
                "ativos no grupo familiar com a mesma faixa etária do plano."
            )

        if plan.audience == PlanAudience.KIDS_JUVENILE and context.kids_juvenile_active_count < 1:
            return "Plano Kids/Juvenil exige aluno menor cadastrado."
        if plan.audience == PlanAudience.ADULT and not context.adult_active:
            return "Plano Adulto exige aluno adulto cadastrado."
        return "Plano não disponível para o perfil selecionado."

    def _clean_selected_products_payload(self):
        selected_products = parse_selected_products(
            self.cleaned_data.get("selected_products_payload")
        )
        if not selected_products:
            self.cleaned_data["selected_products"] = []
            return
        try:
            self.cleaned_data["selected_products"] = resolve_selected_product_items(
                selected_products
            )
        except ValueError as error:
            self.cleaned_data["selected_products"] = []
            self.add_error("selected_products_payload", str(error))
