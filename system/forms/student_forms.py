from datetime import date

from django import forms
from django.forms import formset_factory

from system.models import EmergencyRecord, GuardianRelationship, LgpdRequest, StudentProfile, SystemUser
from system.services.auth.cpf import normalize_cpf
from system.services.lgpd.records import build_term_field_name, get_required_onboarding_terms


class HolderOnboardingForm(forms.Form):
    holder_full_name = forms.CharField(label="Nome completo", max_length=255)
    holder_cpf = forms.CharField(label="CPF", max_length=14)
    holder_email = forms.EmailField(label="E-mail", required=False)
    holder_birth_date = forms.DateField(label="Data de nascimento")
    holder_contact_phone = forms.CharField(label="Telefone", max_length=32, required=False)
    holder_timezone = forms.CharField(label="Timezone", max_length=64, initial="America/Sao_Paulo")
    responsible_same_as_holder = forms.BooleanField(label="Titular e responsavel financeiro", required=False)
    responsible_full_name = forms.CharField(label="Nome do responsavel", max_length=255, required=False)
    responsible_cpf = forms.CharField(label="CPF do responsavel", max_length=14, required=False)
    responsible_email = forms.EmailField(label="E-mail do responsavel", required=False)
    emergency_contact_name = forms.CharField(label="Contato de emergencia", max_length=255, required=False)
    emergency_contact_phone = forms.CharField(label="Telefone de emergencia", max_length=32, required=False)
    emergency_contact_relationship = forms.CharField(label="Vinculo do contato", max_length=128, required=False)
    blood_type = forms.CharField(label="Tipo sanguineo", max_length=16, required=False)
    allergies = forms.CharField(label="Alergias", widget=forms.Textarea, required=False)
    medications = forms.CharField(label="Medicacoes", widget=forms.Textarea, required=False)
    medical_notes = forms.CharField(label="Observacoes medicas", widget=forms.Textarea, required=False)

    def clean_holder_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["holder_cpf"])
        if not cpf:
            raise forms.ValidationError("Informe um CPF valido.")
        if _existing_student_profile_for_cpf(cpf):
            raise forms.ValidationError("Ja existe um aluno ativo com este CPF.")
        return cpf

    def clean_responsible_cpf(self):
        return normalize_cpf(self.cleaned_data.get("responsible_cpf", ""))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("responsible_same_as_holder"):
            return cleaned_data
        self._validate_distinct_responsible(cleaned_data)
        self._validate_responsible_fields(cleaned_data)
        return cleaned_data

    def _validate_distinct_responsible(self, cleaned_data):
        if cleaned_data.get("holder_cpf") == cleaned_data.get("responsible_cpf"):
            raise forms.ValidationError("Use a opcao de mesmo responsavel para o proprio titular.")

    def _validate_responsible_fields(self, cleaned_data):
        missing = []
        for field_name in ("responsible_full_name", "responsible_cpf"):
            if cleaned_data.get(field_name):
                continue
            missing.append(field_name)
        if missing:
            raise forms.ValidationError("Informe os dados do responsavel financeiro.")


class DependentOnboardingForm(forms.Form):
    full_name = forms.CharField(label="Nome completo", max_length=255, required=False)
    cpf = forms.CharField(label="CPF", max_length=14, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    birth_date = forms.DateField(label="Data de nascimento", required=False)
    contact_phone = forms.CharField(label="Telefone", max_length=32, required=False)
    relationship_type = forms.ChoiceField(
        label="Vinculo",
        choices=GuardianRelationship.RELATIONSHIP_CHOICES,
        required=False,
    )
    has_own_credential = forms.BooleanField(label="Possui credencial propria", required=False)
    emergency_contact_name = forms.CharField(label="Contato de emergencia", max_length=255, required=False)
    emergency_contact_phone = forms.CharField(label="Telefone de emergencia", max_length=32, required=False)
    emergency_contact_relationship = forms.CharField(label="Vinculo do contato", max_length=128, required=False)
    blood_type = forms.CharField(label="Tipo sanguineo", max_length=16, required=False)
    allergies = forms.CharField(label="Alergias", widget=forms.Textarea, required=False)
    medications = forms.CharField(label="Medicacoes", widget=forms.Textarea, required=False)
    medical_notes = forms.CharField(label="Observacoes medicas", widget=forms.Textarea, required=False)

    def clean_cpf(self):
        cpf = normalize_cpf(self.cleaned_data.get("cpf", ""))
        if cpf and _existing_student_profile_for_cpf(cpf):
            raise forms.ValidationError("Ja existe um aluno ativo com este CPF.")
        return cpf

    def clean(self):
        cleaned_data = super().clean()
        if not any(cleaned_data.values()):
            self.cleaned_data["skip_form"] = True
            return cleaned_data
        self._validate_required_fields(cleaned_data)
        self._validate_credential_age(cleaned_data)
        return cleaned_data

    def _validate_required_fields(self, cleaned_data):
        required = ("full_name", "cpf", "birth_date", "relationship_type")
        for field_name in required:
            if cleaned_data.get(field_name):
                continue
            self.add_error(field_name, "Campo obrigatorio para dependente.")

    def _validate_credential_age(self, cleaned_data):
        if not cleaned_data.get("has_own_credential"):
            return
        if not cleaned_data.get("birth_date"):
            return
        age = _calculate_age(cleaned_data["birth_date"])
        minimum_age = _get_dependent_credential_min_age()
        if age < minimum_age:
            raise forms.ValidationError("Dependente ainda nao possui idade minima para credencial propria.")


class BaseDependentFormSet(forms.BaseFormSet):
    def __init__(self, *args, holder_cpf=None, **kwargs):
        self.holder_cpf = holder_cpf
        super().__init__(*args, **kwargs)

    def clean(self):
        if any(self.errors):
            return
        cpfs = set()
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get("skip_form"):
                continue
            cpf = form.cleaned_data.get("cpf")
            if cpf in cpfs:
                raise forms.ValidationError("Nao repita o mesmo CPF entre dependentes.")
            if cpf and cpf == self.holder_cpf:
                raise forms.ValidationError("Dependente nao pode usar o mesmo CPF do titular.")
            if cpf:
                cpfs.add(cpf)


DependentOnboardingFormSet = formset_factory(
    DependentOnboardingForm,
    formset=BaseDependentFormSet,
    extra=2,
)


class OnboardingTermsForm(forms.Form):
    confirm_data_accuracy = forms.BooleanField(label="Confirmo que os dados estao corretos")

    def __init__(self, *args, terms=None, **kwargs):
        self.terms = list(terms or [])
        super().__init__(*args, **kwargs)
        self._build_term_fields()

    def _build_term_fields(self):
        for term in self.terms:
            field_name = build_term_field_name(term)
            self.fields[field_name] = forms.BooleanField(
                label=f"Aceito {term.title} v{term.version}",
                required=True,
            )

    def get_accepted_term_ids(self):
        accepted_ids = []
        for term in self.terms:
            if self.cleaned_data.get(build_term_field_name(term)):
                accepted_ids.append(term.id)
        return accepted_ids


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = SystemUser
        fields = ("full_name", "email", "timezone")


class AccountPasswordChangeForm(forms.Form):
    current_password = forms.CharField(label="Senha atual", widget=forms.PasswordInput)
    new_password = forms.CharField(label="Nova senha", widget=forms.PasswordInput)
    new_password_confirmation = forms.CharField(label="Confirmacao da nova senha", widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        self._validate_current_password(cleaned_data)
        self._validate_password_confirmation(cleaned_data)
        return cleaned_data

    def _validate_current_password(self, cleaned_data):
        password = cleaned_data.get("current_password")
        if password and not self.user.check_password(password):
            raise forms.ValidationError("Senha atual invalida.")

    def _validate_password_confirmation(self, cleaned_data):
        if cleaned_data.get("new_password") != cleaned_data.get("new_password_confirmation"):
            raise forms.ValidationError("As senhas nao conferem.")


class LgpdRequestForm(forms.ModelForm):
    class Meta:
        model = LgpdRequest
        fields = ("request_type", "notes")


class StudentRecordForm(forms.Form):
    full_name = forms.CharField(label="Nome completo", max_length=255)
    email = forms.EmailField(label="E-mail", required=False)
    timezone = forms.CharField(label="Timezone", max_length=64, initial="America/Sao_Paulo")
    birth_date = forms.DateField(label="Data de nascimento", required=False)
    contact_phone = forms.CharField(label="Telefone", max_length=32, required=False)
    operational_status = forms.ChoiceField(label="Status", choices=StudentProfile.STATUS_CHOICES)
    self_service_access = forms.BooleanField(label="Acesso proprio", required=False)


class EmergencyRecordForm(forms.ModelForm):
    class Meta:
        model = EmergencyRecord
        fields = (
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "blood_type",
            "allergies",
            "medications",
            "medical_notes",
        )


class GuardianLinkForm(forms.Form):
    responsible_full_name = forms.CharField(label="Nome do responsavel", max_length=255)
    responsible_cpf = forms.CharField(label="CPF do responsavel", max_length=14)
    responsible_email = forms.EmailField(label="E-mail do responsavel", required=False)
    relationship_type = forms.ChoiceField(
        label="Vinculo",
        choices=GuardianRelationship.RELATIONSHIP_CHOICES,
    )
    is_primary = forms.BooleanField(label="Responsavel primario", required=False, initial=True)
    is_financial_responsible = forms.BooleanField(label="Responsavel financeiro", required=False, initial=True)

    def clean_responsible_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["responsible_cpf"])
        if not cpf:
            raise forms.ValidationError("Informe um CPF valido.")
        return cpf


def serialize_step_payload(payload):
    serialized = {}
    for key, value in payload.items():
        serialized[key] = value.isoformat() if isinstance(value, date) else value
    return serialized


def deserialize_step_payload(payload):
    deserialized = {}
    for key, value in payload.items():
        deserialized[key] = _deserialize_value(key, value)
    return deserialized


def _deserialize_value(key, value):
    if key.endswith("_date") and value:
        return date.fromisoformat(value)
    return value


def get_onboarding_terms():
    return list(get_required_onboarding_terms())


def _existing_student_profile_for_cpf(cpf):
    queryset = StudentProfile.objects.filter(user__cpf=cpf)
    return queryset.exists()


def _get_dependent_credential_min_age():
    from system.models import AcademyConfiguration

    return AcademyConfiguration.objects.get().dependent_credential_min_age


def _calculate_age(birth_date):
    today = date.today()
    years = today.year - birth_date.year
    has_had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return years if has_had_birthday else years - 1
