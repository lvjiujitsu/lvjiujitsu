from django import forms

from system.utils import ensure_formatted_cpf, only_digits


class PortalAuthenticationForm(forms.Form):
    identifier = forms.CharField(
        label="CPF ou acesso técnico",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "Digite seu CPF ou acesso técnico",
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

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()
        digits = only_digits(identifier)
        normalized_identifier = identifier.replace(".", "").replace("-", "").replace(" ", "")

        if digits and len(digits) == 11:
            return ensure_formatted_cpf(identifier)

        if digits and len(digits) != 11 and normalized_identifier.isdigit():
            raise forms.ValidationError(
                "Informe um CPF com 11 dígitos ou use seu acesso técnico."
            )

        return identifier


class PortalPasswordResetRequestForm(forms.Form):
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


class PortalSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nova senha",
        strip=False,
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

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1") or ""
        new_password2 = cleaned_data.get("new_password2") or ""

        if not new_password1 or not new_password2:
            return cleaned_data

        if new_password1 != new_password2:
            self.add_error("new_password2", "As senhas não coincidem.")
            return cleaned_data

        return cleaned_data
