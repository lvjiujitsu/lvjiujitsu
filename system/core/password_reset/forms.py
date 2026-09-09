from django import forms
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
    validate_password,
)


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label="Senha nova",
        strip=False,
        help_text=password_validators_help_text_html(),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Digite a senha nova",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Repita a senha nova",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Repita a senha nova",
            }
        ),
    )

    mismatch_message = "As duas senhas precisam ser iguais."

    def __init__(self, *args, account=None, **kwargs):
        self.account = account
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(self.mismatch_message)
        validate_password(password2, self.account)
        return password2


class EmailPasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "O e-mail da sua conta",
            }
        ),
    )

    def get_lookup_value(self):
        return self.cleaned_data.get("email", "")
