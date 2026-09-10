from system.business_rule.constants import CheckoutAction, DependentCardStrategy, DependentFinancialMode
from system.business_rule.selectors.plan_eligibility import is_plan_eligible
from system.business_rule.services.membership import get_active_membership
from system.business_rule.services.registration_checkout import resolve_catalog_plan
from system.business_rule.forms.dependent_form_helpers import (
    build_family_upgrade_context,
    classify_dependent_audience,
    resolve_financial_mode,
)


class DependentFinancialChoiceMixin:
    def _clean_financial_choice(self, cleaned_data):
        mode = resolve_financial_mode(cleaned_data)
        cleaned_data["financial_mode"] = mode

        if mode == DependentFinancialMode.FAMILY_EXISTING:
            cleaned_data["use_family_plan"] = True
            if not self.family_plan_available:
                self.add_error(
                    "use_family_plan",
                    "Não há plano familiar ativo para cobrir este dependente.",
                )
            return

        cleaned_data["use_family_plan"] = False
        plan_id = cleaned_data.get("selected_plan")
        if not plan_id:
            self.add_error("selected_plan", "Selecione um plano para o dependente.")
            return

        legacy_plan, plan_price = resolve_catalog_plan(plan_id)
        plan = legacy_plan if legacy_plan is not None else plan_price
        if plan is None:
            self.add_error("selected_plan", "Selecione um plano válido.")
            return

        if plan_price is not None:
            if mode == DependentFinancialMode.FAMILY_UPGRADE:
                self.add_error(
                    "selected_plan",
                    "Selecione um plano familiar para migrar o titular.",
                )
                return
            dependent_audience = classify_dependent_audience(cleaned_data)
            if dependent_audience and plan_price.tier.audience != dependent_audience:
                self.add_error(
                    "selected_plan",
                    "Selecione um plano compatível com a idade/turma do dependente.",
                )
                return
            cleaned_data["financial_mode"] = DependentFinancialMode.DEPENDENT_OWN
            cleaned_data["selected_plan_obj"] = plan_price
            if not cleaned_data.get("checkout_action"):
                cleaned_data["checkout_action"] = CheckoutAction.PAY_LATER
            return

        if plan.requires_special_authorization:
            self.add_error("selected_plan", "Este plano exige autorização da gestão.")
            return
        if mode != DependentFinancialMode.FAMILY_UPGRADE and plan.is_loyalty_plan:
            self.add_error(
                "selected_plan",
                "Plano veterano exige elegibilidade aprovada pela gestão.",
            )
            return
        if mode == DependentFinancialMode.FAMILY_UPGRADE:
            if not plan.is_family_plan:
                self.add_error(
                    "selected_plan",
                    "Selecione um plano familiar para migrar o titular.",
                )
                return
            context = build_family_upgrade_context(self.owner, cleaned_data)
            if not is_plan_eligible(plan, context):
                self.add_error(
                    "selected_plan",
                    "Plano familiar não elegível para este titular e dependente.",
                )
                return
        elif plan.is_family_plan:
            self.add_error(
                "selected_plan",
                "Plano familiar deve ser selecionado como upgrade do titular.",
            )
            return
        else:
            dependent_audience = classify_dependent_audience(cleaned_data)
            if dependent_audience and plan.audience != dependent_audience:
                self.add_error(
                    "selected_plan",
                    "Selecione um plano compatível com a idade/turma do dependente.",
                )
                return
        cleaned_data["selected_plan_obj"] = plan
        if not cleaned_data.get("checkout_action"):
            cleaned_data["checkout_action"] = CheckoutAction.PAY_LATER

    def _clean_card_strategy(self, cleaned_data):
        strategy = cleaned_data.get("card_strategy") or DependentCardStrategy.NEW_CARD
        mode = cleaned_data.get("financial_mode")
        checkout_action = cleaned_data.get("checkout_action")
        if mode != DependentFinancialMode.DEPENDENT_OWN or checkout_action != CheckoutAction.STRIPE_CARD:
            cleaned_data["card_strategy"] = DependentCardStrategy.NEW_CARD
            return
        if strategy == DependentCardStrategy.SAME_CARD_MERGED:
            owner_membership = get_active_membership(self.owner) if self.owner else None
            if not owner_membership or not owner_membership.stripe_subscription_id:
                self.add_error(
                    "card_strategy",
                    "O responsável não possui assinatura Stripe ativa para fundir a cobrança.",
                )
                strategy = DependentCardStrategy.NEW_CARD
        cleaned_data["card_strategy"] = strategy
