from django import forms

from system.models import OperationalRole
from system.services.access_requests import create_administrative_access_request
from system.utils import ensure_formatted_cpf


class AdministrativeAccessRequestForm(forms.Form):
    full_name = forms.CharField(max_length=255, label="Nome completo")
    cpf = forms.CharField(max_length=14, label="CPF")
    email = forms.EmailField(required=False, label="E-mail")
    phone = forms.CharField(required=False, max_length=20, label="Telefone")
    requested_roles = forms.ModelMultipleChoiceField(
        queryset=OperationalRole.objects.none(),
        required=False,
        label="Áreas solicitadas",
        widget=forms.CheckboxSelectMultiple,
    )
    grant_full_administrative = forms.BooleanField(
        required=False,
        label="Solicitar gestão completa",
    )
    justification = forms.CharField(
        label="Justificativa",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    password = forms.CharField(
        required=False,
        min_length=8,
        strip=False,
        label="Senha inicial",
        widget=forms.PasswordInput(),
    )
    password_confirm = forms.CharField(
        required=False,
        min_length=8,
        strip=False,
        label="Confirmar senha",
        widget=forms.PasswordInput(),
    )

    def __init__(self, *args, **kwargs):
        self.origin = kwargs.pop("origin")
        self.portal_person = kwargs.pop("portal_person", None)
        self.require_password = kwargs.pop("require_password", False)
        super().__init__(*args, **kwargs)
        self.fields["requested_roles"].queryset = OperationalRole.objects.filter(
            is_active=True
        ).order_by("display_name")
        if self.portal_person is not None:
            self.fields["full_name"].initial = self.portal_person.full_name
            self.fields["cpf"].initial = self.portal_person.cpf
            self.fields["email"].initial = self.portal_person.email
            self.fields["phone"].initial = self.portal_person.phone
            for field_name in ("full_name", "cpf", "email", "phone"):
                self.fields[field_name].disabled = True
        if self.require_password:
            self.fields["password"].required = True
            self.fields["password_confirm"].required = True
        else:
            self.fields.pop("password")
            self.fields.pop("password_confirm")

    def clean_cpf(self):
        try:
            return ensure_formatted_cpf(self.cleaned_data.get("cpf", ""))
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error

    def clean(self):
        cleaned_data = super().clean()
        roles = cleaned_data.get("requested_roles") or []
        if not roles and not cleaned_data.get("grant_full_administrative"):
            self.add_error("requested_roles", "Selecione ao menos uma área solicitada.")
        if self.require_password:
            password = cleaned_data.get("password") or ""
            password_confirm = cleaned_data.get("password_confirm") or ""
            if password and password_confirm and password != password_confirm:
                self.add_error("password_confirm", "As senhas não coincidem.")
        return cleaned_data

    def save(self):
        roles = self.cleaned_data.get("requested_roles") or []
        return create_administrative_access_request(
            origin=self.origin,
            full_name=self.cleaned_data["full_name"],
            cpf=self.cleaned_data["cpf"],
            email=self.cleaned_data.get("email", ""),
            phone=self.cleaned_data.get("phone", ""),
            requested_role_codes=[role.code for role in roles],
            grant_full_administrative=self.cleaned_data.get("grant_full_administrative", False),
            justification=self.cleaned_data["justification"],
            requester=self.portal_person,
            password=self.cleaned_data.get("password", ""),
        )


class AdministrativeAccessDecisionForm(forms.Form):
    approved_roles = forms.ModelMultipleChoiceField(
        queryset=OperationalRole.objects.none(),
        required=False,
        label="Papéis aprovados",
        widget=forms.CheckboxSelectMultiple,
    )
    grant_full_administrative = forms.BooleanField(
        required=False,
        label="Conceder administrativo pleno",
    )
    decision_notes = forms.CharField(
        required=False,
        label="Observação da decisão",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        access_request = kwargs.pop("access_request")
        super().__init__(*args, **kwargs)
        queryset = OperationalRole.objects.filter(is_active=True).order_by("display_name")
        self.fields["approved_roles"].queryset = queryset
        requested_codes = access_request.requested_role_codes or []
        self.fields["approved_roles"].initial = list(
            queryset.filter(code__in=requested_codes).values_list("pk", flat=True)
        )
        self.fields["grant_full_administrative"].initial = (
            access_request.grant_full_administrative
        )

    def clean(self):
        cleaned_data = super().clean()
        roles = cleaned_data.get("approved_roles") or []
        if not roles and not cleaned_data.get("grant_full_administrative"):
            self.add_error("approved_roles", "A aprovação precisa conceder ao menos um papel.")
        return cleaned_data
