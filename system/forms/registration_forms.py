from django import forms

from system.models import BloodType, Person, PersonType
from system.services.registration import create_portal_registration
from system.utils import ensure_formatted_cpf


class PortalRegistrationForm(forms.Form):
    base_profile_type_codes = {"student", "guardian", "dependent"}

    registration_profile = forms.ChoiceField(
        choices=(
            ("holder", "Aluno titular"),
            ("guardian", "Responsável"),
            ("other", "Outro"),
        ),
        initial="holder",
    )
    include_dependent = forms.BooleanField(required=False)
    other_type_codes = forms.MultipleChoiceField(required=False)

    holder_name = forms.CharField(required=False, max_length=255)
    holder_cpf = forms.CharField(required=False, max_length=14)
    holder_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    holder_phone = forms.CharField(required=False, max_length=20)
    holder_email = forms.EmailField(required=False)
    holder_password = forms.CharField(required=False, strip=False)
    holder_password_confirm = forms.CharField(required=False, strip=False)
    holder_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    holder_allergies = forms.CharField(required=False)
    holder_injuries = forms.CharField(required=False)
    holder_emergency_contact = forms.CharField(required=False, max_length=255)

    dependent_name = forms.CharField(required=False, max_length=255)
    dependent_cpf = forms.CharField(required=False, max_length=14)
    dependent_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    dependent_password = forms.CharField(required=False, strip=False)
    dependent_password_confirm = forms.CharField(required=False, strip=False)
    dependent_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    dependent_allergies = forms.CharField(required=False)
    dependent_injuries = forms.CharField(required=False)
    dependent_emergency_contact = forms.CharField(required=False, max_length=255)

    guardian_name = forms.CharField(required=False, max_length=255)
    guardian_cpf = forms.CharField(required=False, max_length=14)
    guardian_phone = forms.CharField(required=False, max_length=20)
    guardian_email = forms.EmailField(required=False)
    guardian_password = forms.CharField(required=False, strip=False)
    guardian_password_confirm = forms.CharField(required=False, strip=False)

    student_name = forms.CharField(required=False, max_length=255)
    student_cpf = forms.CharField(required=False, max_length=14)
    student_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    student_password = forms.CharField(required=False, strip=False)
    student_password_confirm = forms.CharField(required=False, strip=False)
    student_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    student_allergies = forms.CharField(required=False)
    student_injuries = forms.CharField(required=False)
    student_emergency_contact = forms.CharField(required=False, max_length=255)

    other_name = forms.CharField(required=False, max_length=255)
    other_cpf = forms.CharField(required=False, max_length=14)
    other_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    other_phone = forms.CharField(required=False, max_length=20)
    other_email = forms.EmailField(required=False)
    other_password = forms.CharField(required=False, strip=False)
    other_password_confirm = forms.CharField(required=False, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_other_type_choices()

    def clean(self):
        cleaned_data = super().clean()
        profile = cleaned_data.get("registration_profile") or "holder"
        include_dependent = cleaned_data.get("include_dependent", False)

        self._clean_required_fields(profile, include_dependent)
        self._clean_cpfs()
        self._clean_other_type_codes(profile)
        self._clean_passwords(profile, include_dependent)
        return cleaned_data

    def save(self):
        return create_portal_registration(self.cleaned_data)

    def _clean_required_fields(self, profile, include_dependent):
        holder_fields = (
            "holder_name",
            "holder_cpf",
            "holder_birthdate",
            "holder_password",
            "holder_password_confirm",
        )
        dependent_fields = (
            "dependent_name",
            "dependent_cpf",
            "dependent_birthdate",
            "dependent_password",
            "dependent_password_confirm",
        )
        guardian_fields = (
            "guardian_name",
            "guardian_cpf",
            "guardian_password",
            "guardian_password_confirm",
        )
        student_fields = (
            "student_name",
            "student_cpf",
            "student_birthdate",
            "student_password",
            "student_password_confirm",
        )
        other_fields = (
            "other_name",
            "other_cpf",
            "other_birthdate",
            "other_password",
            "other_password_confirm",
        )

        if profile == "holder":
            self._require_fields(holder_fields)
            if include_dependent:
                self._require_fields(dependent_fields)
            return

        if profile == "other":
            self._require_fields(other_fields)
            return

        self._require_fields(guardian_fields)
        self._require_fields(student_fields)

    def _require_fields(self, field_names):
        for field_name in field_names:
            value = self.cleaned_data.get(field_name)
            if value in (None, ""):
                self.add_error(field_name, "Campo obrigatório.")

    def _clean_cpfs(self):
        cpf_fields = (
            "holder_cpf",
            "dependent_cpf",
            "guardian_cpf",
            "student_cpf",
            "other_cpf",
        )
        seen_cpfs = {}

        for field_name in cpf_fields:
            value = self.cleaned_data.get(field_name)
            if not value:
                continue

            try:
                formatted_cpf = ensure_formatted_cpf(value)
            except ValueError as error:
                self.add_error(field_name, str(error))
                continue

            if formatted_cpf in seen_cpfs:
                self.add_error(field_name, "CPF duplicado no cadastro.")
                continue

            if Person.objects.filter(cpf=formatted_cpf).exists():
                self.add_error(field_name, "CPF já cadastrado no sistema.")
                continue

            seen_cpfs[formatted_cpf] = field_name
            self.cleaned_data[field_name] = formatted_cpf

    def _clean_other_type_codes(self, profile):
        selected_codes = self.cleaned_data.get("other_type_codes") or []
        available_codes = {code for code, _label in self.fields["other_type_codes"].choices}

        if profile != "other":
            self.cleaned_data["other_type_codes"] = []
            return

        invalid_codes = [code for code in selected_codes if code not in available_codes]
        if invalid_codes:
            self.add_error("other_type_codes", "Seleção de tipos inválida.")
            return

        if available_codes and not selected_codes:
            self.add_error("other_type_codes", "Selecione ao menos um tipo de cadastro.")

    def _clean_passwords(self, profile, include_dependent):
        password_groups = []

        if profile == "holder":
            password_groups.append(("holder_password", "holder_password_confirm", "aluno titular"))
            if include_dependent:
                password_groups.append(("dependent_password", "dependent_password_confirm", "dependente"))
        elif profile == "other":
            password_groups.append(("other_password", "other_password_confirm", "cadastro"))
        else:
            password_groups.append(("guardian_password", "guardian_password_confirm", "responsável"))
            password_groups.append(("student_password", "student_password_confirm", "aluno"))

        for password_field, confirm_field, label in password_groups:
            password = self.cleaned_data.get(password_field) or ""
            confirm_password = self.cleaned_data.get(confirm_field) or ""

            if not password or not confirm_password:
                continue

            if password != confirm_password:
                self.add_error(confirm_field, f"As senhas de {label} não coincidem.")
                continue


    def _configure_other_type_choices(self):
        other_type_queryset = PersonType.objects.filter(is_active=True).exclude(
            code__in=self.base_profile_type_codes
        )
        self.fields["other_type_codes"].choices = [
            (person_type.code, person_type.display_name)
            for person_type in other_type_queryset
        ]
