from datetime import datetime

from django import forms

from system.models import BloodType, ClassGroup, ClassSchedule, Person, PersonType
from system.services.registration import (
    create_portal_registration,
    derive_class_category,
    get_kinship_choices,
    parse_extra_dependents_payload,
    resolve_class_category,
    resolve_class_group,
    resolve_class_schedule,
)
from system.utils import ensure_formatted_cpf


class PortalRegistrationForm(forms.Form):
    registration_profile = forms.ChoiceField(
        choices=(
            ("holder", "Aluno titular"),
            ("guardian", "Responsável"),
            ("other", "Outro"),
        ),
        initial="holder",
    )
    include_dependent = forms.BooleanField(required=False)
    other_type_code = forms.ChoiceField(required=False)
    extra_dependents_payload = forms.CharField(required=False, widget=forms.HiddenInput)

    holder_name = forms.CharField(required=False, max_length=255)
    holder_cpf = forms.CharField(required=False, max_length=14)
    holder_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    holder_phone = forms.CharField(required=False, max_length=20)
    holder_email = forms.EmailField(required=False)
    holder_password = forms.CharField(required=False, strip=False)
    holder_password_confirm = forms.CharField(required=False, strip=False)
    holder_class_category = forms.ChoiceField(required=False)
    holder_class_group = forms.ChoiceField(required=False)
    holder_class_schedule = forms.ChoiceField(required=False)
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
    dependent_email = forms.EmailField(required=False)
    dependent_phone = forms.CharField(required=False, max_length=20)
    dependent_password = forms.CharField(required=False, strip=False)
    dependent_password_confirm = forms.CharField(required=False, strip=False)
    dependent_kinship_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(get_kinship_choices()),
    )
    dependent_kinship_other_label = forms.CharField(required=False, max_length=80)
    dependent_class_category = forms.ChoiceField(required=False)
    dependent_class_group = forms.ChoiceField(required=False)
    dependent_class_schedule = forms.ChoiceField(required=False)
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
    student_email = forms.EmailField(required=False)
    student_phone = forms.CharField(required=False, max_length=20)
    student_password = forms.CharField(required=False, strip=False)
    student_password_confirm = forms.CharField(required=False, strip=False)
    student_kinship_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(get_kinship_choices()),
    )
    student_kinship_other_label = forms.CharField(required=False, max_length=80)
    student_class_category = forms.ChoiceField(required=False)
    student_class_group = forms.ChoiceField(required=False)
    student_class_schedule = forms.ChoiceField(required=False)
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
    other_class_category = forms.ChoiceField(required=False)
    other_class_group = forms.ChoiceField(required=False)
    other_class_schedule = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_is_available = (
            ClassGroup.objects.filter(is_active=True).exists()
            and ClassSchedule.objects.filter(is_active=True).exists()
        )
        self._configure_other_type_choices()
        self._configure_class_choices()

    def clean(self):
        cleaned_data = super().clean()
        profile = cleaned_data.get("registration_profile") or "holder"
        include_dependent = cleaned_data.get("include_dependent", False)
        extra_dependents = self._clean_extra_dependents_payload()
        if profile == "other" or (profile == "holder" and not include_dependent):
            extra_dependents = []
        cleaned_data["extra_dependents"] = extra_dependents

        self._clean_required_fields(profile, include_dependent)
        self._clean_cpfs(extra_dependents)
        self._clean_other_type_code(profile)
        self._clean_passwords(profile, include_dependent, extra_dependents)
        self._clean_class_links(profile, include_dependent, extra_dependents)
        self._clean_kinship(profile, include_dependent, extra_dependents)
        return cleaned_data

    def save(self):
        return create_portal_registration(self.cleaned_data)

    def _configure_other_type_choices(self):
        choices = [("", "Selecione")]
        queryset = PersonType.objects.filter(is_active=True).exclude(
            code__in=("student", "guardian", "dependent")
        )
        choices.extend((item.code, item.display_name) for item in queryset.order_by("display_name"))
        self.fields["other_type_code"].choices = choices

    def _configure_class_choices(self):
        groups = (
            ClassGroup.objects.filter(is_active=True)
            .select_related("class_category")
            .order_by("class_category__display_order", "code")
        )
        schedules = (
            ClassSchedule.objects.filter(is_active=True)
            .select_related("class_group")
            .order_by("class_group__display_name", "display_order", "start_time")
        )
        group_choices = [("", "Selecione")] + [
            (group.pk, f"{group.class_category.display_name} · {group.display_name}")
            for group in groups
        ]
        schedule_choices = [("", "Selecione")] + [
            (schedule.pk, f"{schedule.get_weekday_display()} · {schedule.start_time.strftime('%H:%M')}")
            for schedule in schedules
        ]
        for prefix in ("holder", "dependent", "student", "other"):
            self.fields[f"{prefix}_class_group"].choices = group_choices
            self.fields[f"{prefix}_class_schedule"].choices = schedule_choices
            self.fields[f"{prefix}_class_category"].choices = [("", "Selecione")]

    def _clean_required_fields(self, profile, include_dependent):
        if profile == "holder":
            self._require_fields(
                "holder_name",
                "holder_cpf",
                "holder_birthdate",
                "holder_password",
                "holder_password_confirm",
            )
            if include_dependent:
                self._require_fields(
                    "dependent_name",
                    "dependent_cpf",
                    "dependent_birthdate",
                    "dependent_password",
                    "dependent_password_confirm",
                    "dependent_kinship_type",
                )
            return

        if profile == "guardian":
            self._require_fields(
                "guardian_name",
                "guardian_cpf",
                "guardian_password",
                "guardian_password_confirm",
                "student_name",
                "student_cpf",
                "student_birthdate",
                "student_password",
                "student_password_confirm",
                "student_kinship_type",
            )
            return

        self._require_fields(
            "other_name",
            "other_cpf",
            "other_birthdate",
            "other_password",
            "other_password_confirm",
        )

    def _require_fields(self, *field_names):
        for field_name in field_names:
            value = self.cleaned_data.get(field_name)
            if value in (None, ""):
                self.add_error(field_name, "Campo obrigatório.")

    def _clean_cpfs(self, extra_dependents):
        seen_cpfs = set()
        for field_name in (
            "holder_cpf",
            "dependent_cpf",
            "guardian_cpf",
            "student_cpf",
            "other_cpf",
        ):
            value = self.cleaned_data.get(field_name)
            if not value:
                continue
            self.cleaned_data[field_name] = self._validate_single_cpf(value, field_name, seen_cpfs)

        for index, dependent in enumerate(extra_dependents, start=1):
            value = dependent.get("cpf")
            if not value:
                continue
            dependent["cpf"] = self._validate_single_cpf(value, None, seen_cpfs, index=index)

    def _validate_single_cpf(self, value, field_name, seen_cpfs, index=None):
        try:
            formatted = ensure_formatted_cpf(value)
        except ValueError as error:
            if field_name:
                self.add_error(field_name, str(error))
            else:
                self.add_error(None, f"Dependente adicional {index}: {error}")
            return value

        if formatted in seen_cpfs:
            message = "CPF duplicado no cadastro."
            if field_name:
                self.add_error(field_name, message)
            else:
                self.add_error(None, f"Dependente adicional {index}: {message}")
            return value

        if Person.objects.filter(cpf=formatted).exists():
            message = "CPF já cadastrado no sistema."
            if field_name:
                self.add_error(field_name, message)
            else:
                self.add_error(None, f"Dependente adicional {index}: {message}")
            return value

        seen_cpfs.add(formatted)
        return formatted

    def _clean_other_type_code(self, profile):
        selected_code = self.cleaned_data.get("other_type_code") or ""
        available_codes = {code for code, _label in self.fields["other_type_code"].choices if code}
        if profile != "other":
            self.cleaned_data["other_type_code"] = ""
            return
        if not available_codes:
            self.add_error(
                "other_type_code",
                "Nenhum tipo adicional está disponível para esse cadastro.",
            )
            return
        if available_codes and selected_code not in available_codes:
            self.add_error("other_type_code", "Selecione um tipo de cadastro válido.")
        if available_codes and not selected_code:
            self.add_error("other_type_code", "Selecione um tipo de cadastro.")

    def _clean_passwords(self, profile, include_dependent, extra_dependents):
        groups = []
        if profile == "holder":
            groups.append(("holder_password", "holder_password_confirm", "aluno titular"))
            if include_dependent:
                groups.append(("dependent_password", "dependent_password_confirm", "dependente"))
        elif profile == "guardian":
            groups.append(("guardian_password", "guardian_password_confirm", "responsável"))
            groups.append(("student_password", "student_password_confirm", "dependente"))
        else:
            groups.append(("other_password", "other_password_confirm", "cadastro"))

        for password_field, confirm_field, label in groups:
            self._validate_password_pair(
                self.cleaned_data.get(password_field),
                self.cleaned_data.get(confirm_field),
                confirm_field,
                label,
            )

        for index, dependent in enumerate(extra_dependents, start=1):
            self._validate_password_pair(
                dependent.get("password"),
                dependent.get("password_confirm"),
                None,
                f"dependente adicional {index}",
            )

    def _validate_password_pair(self, password, confirm_password, error_field, label):
        if not password or not confirm_password:
            return
        if password != confirm_password:
            message = f"As senhas de {label} não coincidem."
            if error_field:
                self.add_error(error_field, message)
            else:
                self.add_error(None, message)

    def _clean_class_links(self, profile, include_dependent, extra_dependents):
        if profile == "holder":
            self._resolve_class_triplet("holder", required=self.catalog_is_available)
            if include_dependent:
                self._resolve_class_triplet("dependent", required=self.catalog_is_available)
        elif profile == "guardian":
            self._resolve_class_triplet("student", required=self.catalog_is_available)
        else:
            self._resolve_class_triplet("other", required=False)

        for index, dependent in enumerate(extra_dependents, start=1):
            category = resolve_class_category(dependent.get("class_category"))
            group = resolve_class_group(dependent.get("class_group"))
            schedule = resolve_class_schedule(dependent.get("class_schedule"))
            if not self.catalog_is_available and not any([category, group, schedule]):
                dependent["class_category"] = None
                dependent["class_group"] = None
                dependent["class_schedule"] = None
                continue
            if not group or not schedule:
                self.add_error(None, f"Dependente adicional {index} precisa informar turma e horário.")
                continue
            if schedule.class_group_id != group.id:
                self.add_error(
                    None,
                    f"Dependente adicional {index} possui horário incompatível com a turma.",
                )
                continue
            dependent["class_category"] = derive_class_category(
                class_group=group,
                explicit_category=category,
            )
            dependent["class_group"] = group
            dependent["class_schedule"] = schedule

    def _resolve_class_triplet(self, prefix, required):
        category_field = f"{prefix}_class_category"
        group_field = f"{prefix}_class_group"
        schedule_field = f"{prefix}_class_schedule"

        raw_category = self.cleaned_data.get(category_field)
        raw_group = self.cleaned_data.get(group_field)
        raw_schedule = self.cleaned_data.get(schedule_field)

        if not any([raw_category, raw_group, raw_schedule]) and not required:
            self.cleaned_data[category_field] = None
            self.cleaned_data[group_field] = None
            self.cleaned_data[schedule_field] = None
            return

        if required and not self.catalog_is_available:
            self.cleaned_data[category_field] = None
            self.cleaned_data[group_field] = None
            self.cleaned_data[schedule_field] = None
            return

        category = resolve_class_category(raw_category)
        group = resolve_class_group(raw_group)
        schedule = resolve_class_schedule(raw_schedule)

        if required and not group:
            self.add_error(group_field, "Selecione a turma.")
        if required and not schedule:
            self.add_error(schedule_field, "Selecione o horário.")
        if group and schedule and schedule.class_group_id != group.id:
            self.add_error(schedule_field, "O horário não pertence à turma escolhida.")

        self.cleaned_data[category_field] = derive_class_category(
            class_group=group,
            explicit_category=category,
        )
        self.cleaned_data[group_field] = group
        self.cleaned_data[schedule_field] = schedule

    def _clean_kinship(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == "holder" and include_dependent:
            prefixes.append("dependent")
        if profile == "guardian":
            prefixes.append("student")

        for prefix in prefixes:
            kinship_type = self.cleaned_data.get(f"{prefix}_kinship_type") or ""
            other_label = (self.cleaned_data.get(f"{prefix}_kinship_other_label") or "").strip()
            if kinship_type == "other" and not other_label:
                self.add_error(
                    f"{prefix}_kinship_other_label",
                    "Informe o grau de parentesco.",
                )

        for index, dependent in enumerate(extra_dependents, start=1):
            if dependent.get("kinship_type") == "other" and not (dependent.get("kinship_other_label") or "").strip():
                self.add_error(None, f"Dependente adicional {index}: informe o grau de parentesco.")

    def _clean_extra_dependents_payload(self):
        payload = parse_extra_dependents_payload(self.cleaned_data.get("extra_dependents_payload"))
        cleaned_dependents = []
        for index, dependent in enumerate(payload, start=1):
            birth_date_raw = dependent.get("birth_date") or ""
            birth_date = None
            if birth_date_raw:
                try:
                    birth_date = datetime.strptime(birth_date_raw, "%d/%m/%Y").date()
                except ValueError:
                    self.add_error(
                        None,
                        f"Dependente adicional {index}: data de nascimento inválida.",
                    )
            cleaned_dependents.append(
                {
                    "full_name": (dependent.get("full_name") or "").strip(),
                    "cpf": (dependent.get("cpf") or "").strip(),
                    "birth_date": birth_date,
                    "email": (dependent.get("email") or "").strip(),
                    "phone": (dependent.get("phone") or "").strip(),
                    "password": dependent.get("password") or "",
                    "password_confirm": dependent.get("password_confirm") or "",
                    "kinship_type": dependent.get("kinship_type") or "",
                    "kinship_other_label": (dependent.get("kinship_other_label") or "").strip(),
                    "class_category": dependent.get("class_category") or "",
                    "class_group": dependent.get("class_group") or "",
                    "class_schedule": dependent.get("class_schedule") or "",
                    "blood_type": dependent.get("blood_type") or "",
                    "allergies": dependent.get("allergies") or "",
                    "previous_injuries": dependent.get("injuries") or dependent.get("previous_injuries") or "",
                    "emergency_contact": dependent.get("emergency_contact") or "",
                }
            )
        return cleaned_dependents
