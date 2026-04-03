from django import forms

from system.models import FinancialPlan, StripePlanPriceMap


class StripePlanPriceMapForm(forms.ModelForm):
    class Meta:
        model = StripePlanPriceMap
        fields = (
            "plan",
            "stripe_product_id",
            "stripe_price_id",
            "product_name",
            "lookup_key",
            "currency",
            "amount",
            "recurring_interval",
            "recurring_interval_count",
            "livemode",
            "is_active",
            "is_current",
            "is_legacy",
            "supports_pause_collection",
            "valid_from",
            "valid_until",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = FinancialPlan.objects.order_by("name")
