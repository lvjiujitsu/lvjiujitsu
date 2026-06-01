from django import forms

from system.models.plan import (
    BillingCycle,
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)


PLAN_STATUS_CHOICES = (
    ("", "Todos"),
    ("active", "Ativos"),
    ("inactive", "Inativos"),
)


def _empty_choice(label):
    return [("", label)]


class PlanForm(forms.ModelForm):
    identity_field_names = (
        "code",
        "display_name",
        "description",
        "display_order",
        "is_active",
    )
    segmentation_field_names = (
        "audience",
        "weekly_frequency",
        "billing_cycle",
        "payment_method",
        "is_family_plan",
        "is_loyalty_plan",
        "requires_special_authorization",
    )
    pricing_field_names = (
        "price",
        "monthly_reference_price",
        "base_monthly_net_price",
        "cycle_discount_percentage",
        "teacher_commission_percentage",
    )
    gateway_field_names = (
        "gateway_code",
        "gateway_fixed_fee",
        "gateway_percentage_fee",
    )

    class Meta:
        model = SubscriptionPlan
        fields = (
            "code",
            "display_name",
            "audience",
            "weekly_frequency",
            "billing_cycle",
            "payment_method",
            "is_family_plan",
            "is_loyalty_plan",
            "requires_special_authorization",
            "price",
            "monthly_reference_price",
            "base_monthly_net_price",
            "gateway_code",
            "gateway_fixed_fee",
            "gateway_percentage_fee",
            "cycle_discount_percentage",
            "teacher_commission_percentage",
            "description",
            "display_order",
            "is_active",
        )
        labels = {
            "code": "Código técnico",
            "display_name": "Nome exibido",
            "audience": "Público",
            "weekly_frequency": "Frequência semanal",
            "billing_cycle": "Ciclo de cobrança",
            "payment_method": "Meio de pagamento",
            "is_family_plan": "Plano familiar",
            "is_loyalty_plan": "Plano fidelidade",
            "requires_special_authorization": "Exige autorização especial",
            "price": "Preço cobrado",
            "monthly_reference_price": "Referência mensal",
            "base_monthly_net_price": "Valor líquido mensal desejado",
            "gateway_code": "Gateway",
            "gateway_fixed_fee": "Taxa fixa do gateway",
            "gateway_percentage_fee": "Taxa percentual do gateway",
            "cycle_discount_percentage": "Desconto do ciclo",
            "teacher_commission_percentage": "Repasse do professor",
            "description": "Descrição",
            "display_order": "Ordem de exibição",
            "is_active": "Plano ativo",
        }
        widgets = {
            "audience": forms.Select(
                choices=_empty_choice("Selecione") + list(PlanAudience.choices)
            ),
            "weekly_frequency": forms.Select(
                choices=_empty_choice("Selecione") + list(PlanWeeklyFrequency.choices)
            ),
            "billing_cycle": forms.Select(
                choices=_empty_choice("Selecione") + list(BillingCycle.choices)
            ),
            "payment_method": forms.Select(
                choices=_empty_choice("Selecione") + list(PlanPaymentMethod.choices)
            ),
            "price": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}
            ),
            "monthly_reference_price": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}
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
            "description": forms.Textarea(attrs={"rows": 4}),
            "display_order": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audience"].required = False
        self.fields["audience"].initial = PlanAudience.ADULT
        self.fields["monthly_reference_price"].required = False
        self.fields["base_monthly_net_price"].required = False
        self.fields["description"].required = False
        self.fields["gateway_code"].widget.attrs.update(
            {"placeholder": "Ex: asaas_pix, asaas_card, stripe_card"}
        )
        self.fields["price"].help_text = (
            "Quando o valor líquido mensal estiver preenchido, o preço é recalculado ao salvar."
        )
        self.fields["monthly_reference_price"].help_text = (
            "Calculado automaticamente para ciclos maiores que mensal quando há valor líquido mensal."
        )
        self.fields["teacher_commission_percentage"].help_text = (
            "Percentual inteiro ou decimal. Ex: 10 = 10%."
        )
        self.order_fields(
            [
                "code",
                "display_name",
                "description",
                "display_order",
                "is_active",
                "audience",
                "weekly_frequency",
                "billing_cycle",
                "payment_method",
                "is_family_plan",
                "is_loyalty_plan",
                "requires_special_authorization",
                "price",
                "monthly_reference_price",
                "base_monthly_net_price",
                "cycle_discount_percentage",
                "teacher_commission_percentage",
                "gateway_code",
                "gateway_fixed_fee",
                "gateway_percentage_fee",
            ]
        )

    @property
    def identity_fields(self):
        return self._bound_fields(self.identity_field_names)

    @property
    def segmentation_fields(self):
        return self._bound_fields(self.segmentation_field_names)

    @property
    def pricing_fields(self):
        return self._bound_fields(self.pricing_field_names)

    @property
    def gateway_fields(self):
        return self._bound_fields(self.gateway_field_names)

    def clean_audience(self):
        return self.cleaned_data.get("audience") or PlanAudience.ADULT

    def _bound_fields(self, field_names):
        return [self[name] for name in field_names]


class PlanListFilterForm(forms.Form):
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
    billing_cycle = forms.ChoiceField(
        required=False,
        label="Ciclo",
        choices=_empty_choice("Todos") + list(BillingCycle.choices),
    )
    payment_method = forms.ChoiceField(
        required=False,
        label="Pagamento",
        choices=_empty_choice("Todos") + list(PlanPaymentMethod.choices),
    )
    gateway_code = forms.ChoiceField(required=False, label="Gateway")
    is_active = forms.ChoiceField(
        required=False,
        label="Status",
        choices=PLAN_STATUS_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        gateway_codes = (
            SubscriptionPlan.objects.exclude(gateway_code="")
            .order_by("gateway_code")
            .values_list("gateway_code", flat=True)
            .distinct()
        )
        self.fields["gateway_code"].choices = _empty_choice("Todos") + [
            (gateway_code, gateway_code) for gateway_code in gateway_codes
        ]
