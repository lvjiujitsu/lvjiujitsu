from django import forms

from system.models.plan import SubscriptionPlan


class PlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "code",
            "display_name",
            "billing_cycle",
            "price",
            "description",
            "display_order",
            "is_active",
        )
