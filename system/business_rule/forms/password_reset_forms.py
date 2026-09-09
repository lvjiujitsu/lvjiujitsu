from django import forms

from system.core.documents import ensure_formatted_cpf
from system.core.password_reset import PasswordResetConfirmForm


class PasswordResetRequestForm(forms.Form):
    cpf = forms.CharField(
        label="CPF",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Digite seu CPF",
                "autocomplete": "username",
            }
        ),
    )

    def clean_cpf(self):
        try:
            return ensure_formatted_cpf(self.cleaned_data["cpf"].strip())
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error

    def get_lookup_value(self):
        return self.cleaned_data.get("cpf", "")


__all__ = ["PasswordResetConfirmForm", "PasswordResetRequestForm"]
