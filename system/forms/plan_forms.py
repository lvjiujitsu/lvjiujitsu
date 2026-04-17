from django import forms

from system.models.plan import PlanPaymentMethod, SubscriptionPlan


class PlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "code",
            "display_name",
            "billing_cycle",
            "payment_method",
            "price",
            "monthly_reference_price",
            "is_family_plan",
            "description",
            "display_order",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].required = False
        self.fields["payment_method"].initial = PlanPaymentMethod.CREDIT_CARD

    def clean_payment_method(self):
        return self.cleaned_data.get("payment_method") or PlanPaymentMethod.CREDIT_CARD
