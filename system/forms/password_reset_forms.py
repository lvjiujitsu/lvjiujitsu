from django import forms
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
    validate_password,
)

from system.utils import ensure_formatted_cpf


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


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nova senha",
        strip=False,
        help_text=password_validators_help_text_html(),
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Digite a nova senha",
                "autocomplete": "new-password",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Confirmar nova senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Repita a nova senha",
                "autocomplete": "new-password",
            }
        ),
    )

    def __init__(self, *args, account=None, **kwargs):
        self.account = account
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem.")
        validate_password(password2, self.account)
        return password2
