from django import forms

from system.business_rule.models import OperationalRole, PixKeyType
from system.business_rule.services.access_requests import create_administrative_access_request
from system.core.documents import ensure_formatted_cpf


TRAINING_INTENT_NONE = "none"
TRAINING_INTENT_STUDENT = "student"
COMPENSATION_NONE = "none"
COMPENSATION_BARTER = "barter"
COMPENSATION_PIX = "pix"


class AdministrativeAccessRequestForm(forms.Form):
    full_name = forms.CharField(max_length=255, label="Nome completo")
    cpf = forms.CharField(max_length=14, label="CPF")
    email = forms.EmailField(required=False, label="E-mail")
    phone = forms.CharField(required=False, max_length=20, label="Telefone")
    training_intent = forms.ChoiceField(
        choices=(
            (TRAINING_INTENT_NONE, "Somente acesso administrativo"),
            (TRAINING_INTENT_STUDENT, "Administrativo e aluno"),
        ),
        label="Como esse perfil será usado?",
    )
    compensation_preference = forms.ChoiceField(
        choices=(
            (COMPENSATION_NONE, "Sem recebimento"),
            (COMPENSATION_BARTER, "Permuta"),
            (COMPENSATION_PIX, "Receber por PIX"),
        ),
        label="Compensação prevista",
    )
    pix_key_type = forms.ChoiceField(
        choices=(("", "Selecione"),) + tuple(PixKeyType.choices),
        required=False,
        label="Tipo da chave PIX",
    )
    pix_key = forms.CharField(required=False, max_length=140, label="Chave PIX")
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
        if cleaned_data.get("compensation_preference") == COMPENSATION_PIX:
            if not cleaned_data.get("pix_key_type"):
                self.add_error("pix_key_type", "Selecione o tipo da chave PIX.")
            if not (cleaned_data.get("pix_key") or "").strip():
                self.add_error("pix_key", "Informe a chave PIX.")
        if self.require_password:
            password = cleaned_data.get("password") or ""
            password_confirm = cleaned_data.get("password_confirm") or ""
            if password and password_confirm and password != password_confirm:
                self.add_error("password_confirm", "As senhas não coincidem.")
        return cleaned_data

    def get_request_payload(self):
        return {
            "training_intent": self.cleaned_data.get("training_intent") or TRAINING_INTENT_NONE,
            "compensation_preference": (
                self.cleaned_data.get("compensation_preference") or COMPENSATION_NONE
            ),
            "pix_key_type": self.cleaned_data.get("pix_key_type") or "",
            "pix_key": (self.cleaned_data.get("pix_key") or "").strip(),
        }

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
            request_payload=self.get_request_payload(),
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
