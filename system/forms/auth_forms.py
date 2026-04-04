from django import forms
from django.contrib.auth.forms import AuthenticationForm


class PortalAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="CPF ou usuário",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "Digite seu CPF ou usuário",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Digite sua senha",
                "autocomplete": "current-password",
            }
        ),
    )
