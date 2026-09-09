from django import forms

from system.business_rule.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanPrice,
    PlanTier,
    PlanWeeklyFrequency,
)


PLAN_TIER_STATUS_CHOICES = (
    ("", "Todos"),
    ("active", "Ativos"),
    ("inactive", "Inativos"),
)


def _empty_choice(label):
    return [("", label)]


class PlanTierForm(forms.ModelForm):
    class Meta:
        model = PlanTier
        fields = (
            "code",
            "display_name",
            "audience",
            "weekly_frequency",
            "family_discount_percentage",
            "display_order",
            "is_active",
        )
        labels = {
            "code": "Código técnico",
            "display_name": "Nome exibido",
            "audience": "Público",
            "weekly_frequency": "Frequência semanal",
            "family_discount_percentage": "Desconto família",
            "display_order": "Ordem de exibição",
            "is_active": "Tier ativo",
        }
        widgets = {
            "audience": forms.Select(
                choices=_empty_choice("Selecione") + list(PlanAudience.choices)
            ),
            "weekly_frequency": forms.Select(
                choices=_empty_choice("Selecione") + list(PlanWeeklyFrequency.choices)
            ),
            "family_discount_percentage": forms.NumberInput(
                attrs={"step": "0.0001", "min": "0", "inputmode": "decimal"}
            ),
            "display_order": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audience"].required = False
        self.fields["audience"].initial = PlanAudience.ADULT
        self.fields["family_discount_percentage"].help_text = (
            "Decimal puro. Ex: 0.18 = 18%. Aplicado quando 2+ pessoas do "
            "grupo familiar compartilham este tier."
        )

    def clean_audience(self):
        return self.cleaned_data.get("audience") or PlanAudience.ADULT


class PlanTierListFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Busca")
    audience = forms.ChoiceField(
        required=False,
        label="Público",
        choices=_empty_choice("Todos") + list(PlanAudience.choices),
    )
    weekly_frequency = forms.TypedChoiceField(
        required=False,
        label="Frequência",
        choices=_empty_choice("Todas") + list(PlanWeeklyFrequency.choices),
        coerce=int,
        empty_value=None,
    )
    is_active = forms.ChoiceField(
        required=False,
        label="Status",
        choices=PLAN_TIER_STATUS_CHOICES,
    )


class PlanPriceForm(forms.ModelForm):
    class Meta:
        model = PlanPrice
        fields = (
            "tier",
            "payment_method",
            "billing_cycle",
            "gateway_code",
            "base_monthly_net_price",
            "cycle_discount_percentage",
            "gateway_fixed_fee",
            "gateway_percentage_fee",
            "teacher_commission_percentage",
            "is_active",
        )
        labels = {
            "tier": "Tier comercial",
            "payment_method": "Meio de pagamento",
            "billing_cycle": "Ciclo de cobrança",
            "gateway_code": "Gateway",
            "base_monthly_net_price": "Valor líquido mensal desejado",
            "cycle_discount_percentage": "Desconto do ciclo",
            "gateway_fixed_fee": "Taxa fixa do gateway",
            "gateway_percentage_fee": "Taxa percentual do gateway",
            "teacher_commission_percentage": "Repasse do professor",
            "is_active": "Preço ativo",
        }
        widgets = {
            "payment_method": forms.Select(
                choices=_empty_choice("Selecione") + list(PlanPaymentMethod.choices)
            ),
            "billing_cycle": forms.Select(
                choices=_empty_choice("Selecione") + list(BillingCycle.choices)
            ),
            "base_monthly_net_price": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}
            ),
            "gateway_fixed_fee": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}
            ),
            "gateway_percentage_fee": forms.NumberInput(
                attrs={"step": "0.0001", "min": "0", "inputmode": "decimal"}
            ),
            "cycle_discount_percentage": forms.NumberInput(
                attrs={"step": "0.0001", "min": "0", "inputmode": "decimal"}
            ),
            "teacher_commission_percentage": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.locked_tier = kwargs.pop("locked_tier", None)
        super().__init__(*args, **kwargs)
        self.fields["gateway_code"].widget.attrs.update(
            {"placeholder": "Ex: asaas_pix, asaas_card, stripe_card"}
        )
        self.fields["base_monthly_net_price"].help_text = (
            "O preço final é sempre recalculado a partir deste valor ao salvar."
        )
        self.fields["teacher_commission_percentage"].help_text = (
            "Percentual inteiro ou decimal. Ex: 10 = 10%."
        )
        if self.locked_tier is not None:
            self.fields["tier"].initial = self.locked_tier
            self.fields["tier"].widget = forms.HiddenInput()
            self.fields["tier"].required = False
        is_locked = bool(
            self.instance.pk and self.instance.is_referenced_by_membership
        )
        if is_locked:
            pricing_field_names = (
                "tier",
                "payment_method",
                "billing_cycle",
                "base_monthly_net_price",
                "cycle_discount_percentage",
                "gateway_fixed_fee",
                "gateway_percentage_fee",
            )
            for field_name in pricing_field_names:
                self.fields[field_name].disabled = True
            self.fields["teacher_commission_percentage"].help_text = (
                (self.fields["teacher_commission_percentage"].help_text or "")
                + " Preço já usado por uma assinatura: campos de precificação são somente leitura."
            )

    def clean(self):
        cleaned_data = super().clean()
        if self.locked_tier is not None:
            cleaned_data["tier"] = self.locked_tier
        return cleaned_data
