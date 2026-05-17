from django import forms

from system.models.plan import PlanAudience, SubscriptionPlan


class PlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "code",
            "display_name",
            "audience",
            "is_family_plan",
            "is_loyalty_plan",
            "description",
            "display_order",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audience"].required = False
        self.fields["audience"].initial = PlanAudience.ADULT

    def clean_audience(self):
        return self.cleaned_data.get("audience") or PlanAudience.ADULT
