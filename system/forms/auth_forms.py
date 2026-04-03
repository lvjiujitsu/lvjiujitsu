from django import forms

from system.services.auth.cpf import normalize_cpf


class CpfLoginForm(forms.Form):
    cpf = forms.CharField(label="CPF", max_length=14)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def clean_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["cpf"])
        if not cpf:
            raise forms.ValidationError("Informe um CPF valido.")
        return cpf


class PasswordActionRequestForm(forms.Form):
    cpf = forms.CharField(label="CPF", max_length=14)

    def clean_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["cpf"])
        if not cpf:
            raise forms.ValidationError("Informe um CPF valido.")
        return cpf


class PasswordActionConfirmForm(forms.Form):
    password = forms.CharField(label="Nova senha", widget=forms.PasswordInput)
    password_confirmation = forms.CharField(label="Confirmacao da senha", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise forms.ValidationError("As senhas nao conferem.")
        return cleaned_data
