from decimal import Decimal

from django import forms


class WithdrawalRequestForm(forms.Form):
    amount = forms.DecimalField(
        label="Valor (R$)",
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
    )
    notes = forms.CharField(
        label="Justificativa",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=500,
    )
