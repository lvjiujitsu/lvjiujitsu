from django import forms

from system.models.plan import (
    PlanAudience,
    PlanPaymentMethod,
    PlanWeeklyFrequency,
    SubscriptionPlan,
)


class PlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "code",
            "display_name",
            "audience",
            "weekly_frequency",
            "billing_cycle",
            "payment_method",
            "price",
            "monthly_reference_price",
            "is_family_plan",
            "teacher_commission_percentage",
            "requires_special_authorization",
            "description",
            "display_order",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].required = False
        self.fields["payment_method"].initial = PlanPaymentMethod.CREDIT_CARD
        self.fields["audience"].required = False
        self.fields["audience"].initial = PlanAudience.ADULT
        self.fields["weekly_frequency"].required = False
        self.fields["weekly_frequency"].initial = PlanWeeklyFrequency.FIVE_TIMES
        self.fields["teacher_commission_percentage"].required = False

    def clean_payment_method(self):
        return self.cleaned_data.get("payment_method") or PlanPaymentMethod.CREDIT_CARD

    def clean_audience(self):
        return self.cleaned_data.get("audience") or PlanAudience.ADULT

    def clean_weekly_frequency(self):
        return self.cleaned_data.get("weekly_frequency") or PlanWeeklyFrequency.FIVE_TIMES

    def clean_teacher_commission_percentage(self):
        value = self.cleaned_data.get("teacher_commission_percentage")
        if value in (None, ""):
            return 0
        return value
