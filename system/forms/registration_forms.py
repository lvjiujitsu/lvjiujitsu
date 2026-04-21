from datetime import datetime

from django import forms

from system.models import (
    BiologicalSex,
    BloodType,
    ClassGroup,
    JiuJitsuBelt,
    MartialArt,
    Person,
    PersonType,
    SubscriptionPlan,
)
from system.models.class_membership import get_class_group_eligibility_error
from system.constants import (
    CheckoutAction,
    RegistrationProfile,
    STUDENT_PORTAL_PERSON_TYPE_CODES,
)
from system.services.class_overview import get_public_class_group_choice_options
from system.services.registration import (
    create_portal_registration,
    get_kinship_choices,
    parse_extra_dependents_payload,
    resolve_class_groups,
)
from system.services.financial_transactions import resolve_checkout_action_for_plan
from system.utils import ensure_formatted_cpf


class PortalRegistrationForm(forms.Form):
    registration_profile = forms.ChoiceField(
        choices=(
            (RegistrationProfile.HOLDER, "Aluno titular"),
            (RegistrationProfile.GUARDIAN, "Responsável"),
            (RegistrationProfile.OTHER, "Outro"),
        ),
        initial=RegistrationProfile.HOLDER,
    )
    include_dependent = forms.BooleanField(required=False)
    other_type_code = forms.ChoiceField(required=False)
    extra_dependents_payload = forms.CharField(required=False, widget=forms.HiddenInput)

    holder_name = forms.CharField(required=False, max_length=255)
    holder_cpf = forms.CharField(required=False, max_length=14)
    holder_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    holder_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    holder_phone = forms.CharField(required=False, max_length=20)
    holder_email = forms.EmailField(required=False)
    holder_password = forms.CharField(required=False, strip=False)
    holder_password_confirm = forms.CharField(required=False, strip=False)
    holder_class_groups = forms.MultipleChoiceField(required=False)
    holder_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    holder_allergies = forms.CharField(required=False)
    holder_injuries = forms.CharField(required=False)
    holder_emergency_contact = forms.CharField(required=False, max_length=255)
    holder_martial_art = forms.ChoiceField(
        required=False,
        choices=[("", "Não possui")] + list(MartialArt.choices),
    )
    holder_martial_art_graduation = forms.CharField(required=False, max_length=120)
    holder_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    holder_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)

    dependent_name = forms.CharField(required=False, max_length=255)
    dependent_cpf = forms.CharField(required=False, max_length=14)
    dependent_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    dependent_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    dependent_email = forms.EmailField(required=False)
    dependent_phone = forms.CharField(required=False, max_length=20)
    dependent_password = forms.CharField(required=False, strip=False)
    dependent_password_confirm = forms.CharField(required=False, strip=False)
    dependent_kinship_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(get_kinship_choices()),
    )
    dependent_kinship_other_label = forms.CharField(required=False, max_length=80)
    dependent_class_groups = forms.MultipleChoiceField(required=False)
    dependent_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    dependent_allergies = forms.CharField(required=False)
    dependent_injuries = forms.CharField(required=False)
    dependent_emergency_contact = forms.CharField(required=False, max_length=255)
    dependent_martial_art = forms.ChoiceField(
        required=False,
        choices=[("", "Não possui")] + list(MartialArt.choices),
    )
    dependent_martial_art_graduation = forms.CharField(required=False, max_length=120)
    dependent_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    dependent_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)

    guardian_name = forms.CharField(required=False, max_length=255)
    guardian_cpf = forms.CharField(required=False, max_length=14)
    guardian_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    guardian_phone = forms.CharField(required=False, max_length=20)
    guardian_email = forms.EmailField(required=False)
    guardian_password = forms.CharField(required=False, strip=False)
    guardian_password_confirm = forms.CharField(required=False, strip=False)

    student_name = forms.CharField(required=False, max_length=255)
    student_cpf = forms.CharField(required=False, max_length=14)
    student_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    student_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    student_email = forms.EmailField(required=False)
    student_phone = forms.CharField(required=False, max_length=20)
    student_password = forms.CharField(required=False, strip=False)
    student_password_confirm = forms.CharField(required=False, strip=False)
    student_kinship_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(get_kinship_choices()),
    )
    student_kinship_other_label = forms.CharField(required=False, max_length=80)
    student_class_groups = forms.MultipleChoiceField(required=False)
    student_blood_type = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BloodType.choices),
    )
    student_allergies = forms.CharField(required=False)
    student_injuries = forms.CharField(required=False)
    student_emergency_contact = forms.CharField(required=False, max_length=255)
    student_martial_art = forms.ChoiceField(
        required=False,
        choices=[("", "Não possui")] + list(MartialArt.choices),
    )
    student_martial_art_graduation = forms.CharField(required=False, max_length=120)
    student_jiu_jitsu_belt = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
    )
    student_jiu_jitsu_stripes = forms.IntegerField(required=False, min_value=0, max_value=4)

    selected_plan = forms.IntegerField(required=False)
    selected_products_payload = forms.CharField(required=False, widget=forms.HiddenInput)
    checkout_action = forms.ChoiceField(
        required=False,
        choices=(
            (CheckoutAction.STRIPE, "Pagar com cartão"),
            (CheckoutAction.PIX, "Pagar com PIX"),
            (CheckoutAction.PAY_LATER, "Concluir e pagar depois"),
        ),
        initial=CheckoutAction.PAY_LATER,
    )

    other_name = forms.CharField(required=False, max_length=255)
    other_cpf = forms.CharField(required=False, max_length=14)
    other_birthdate = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    other_biological_sex = forms.ChoiceField(
        required=False,
        choices=[("", "Selecione")] + list(BiologicalSex.choices),
    )
    other_phone = forms.CharField(required=False, max_length=20)
    other_email = forms.EmailField(required=False)
    other_password = forms.CharField(required=False, strip=False)
    other_password_confirm = forms.CharField(required=False, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_is_available = ClassGroup.objects.filter(is_active=True).exists()
        self._configure_other_type_choices()
        self._configure_class_choices()

    def clean(self):
        cleaned_data = super().clean()
        profile = cleaned_data.get("registration_profile") or RegistrationProfile.HOLDER
        include_dependent = cleaned_data.get("include_dependent", False)
        extra_dependents = self._clean_extra_dependents_payload()
        if profile == RegistrationProfile.OTHER or (
            profile == RegistrationProfile.HOLDER and not include_dependent
        ):
            extra_dependents = []
        cleaned_data["extra_dependents"] = extra_dependents

        self._clean_required_fields(profile, include_dependent)
        self._clean_cpfs(extra_dependents)
        self._clean_other_type_code(profile)
        self._clean_passwords(profile, include_dependent, extra_dependents)
        self._clean_class_links(profile, include_dependent, extra_dependents)
        self._clean_plan_selection(profile, include_dependent, extra_dependents)
        self._clean_kinship(profile, include_dependent, extra_dependents)
        self._clean_martial_background(profile, include_dependent, extra_dependents)
        if not self.cleaned_data.get("checkout_action"):
            self.cleaned_data["checkout_action"] = CheckoutAction.PAY_LATER
        return cleaned_data

    def save(self):
        return create_portal_registration(self.cleaned_data)

    def _configure_other_type_choices(self):
        choices = [("", "Selecione")]
        queryset = PersonType.objects.filter(is_active=True).exclude(
            code__in=STUDENT_PORTAL_PERSON_TYPE_CODES
        )
        choices.extend((item.code, item.display_name) for item in queryset.order_by("display_name"))
        self.fields["other_type_code"].choices = choices

    def _configure_class_choices(self):
        group_choices = [("", "Selecione")] + get_public_class_group_choice_options()
        for prefix in ("holder", "dependent", "student"):
            self.fields[f"{prefix}_class_groups"].choices = group_choices

    def _clean_required_fields(self, profile, include_dependent):
        if profile == RegistrationProfile.HOLDER:
            self._require_fields(
                "holder_name",
                "holder_cpf",
                "holder_birthdate",
                "holder_biological_sex",
                "holder_password",
                "holder_password_confirm",
            )
            if include_dependent:
                self._require_fields(
                    "dependent_name",
                    "dependent_cpf",
                    "dependent_birthdate",
                    "dependent_biological_sex",
                    "dependent_password",
                    "dependent_password_confirm",
                    "dependent_kinship_type",
                )
            return

        if profile == RegistrationProfile.GUARDIAN:
            self._require_fields(
                "guardian_name",
                "guardian_cpf",
                "guardian_password",
                "guardian_password_confirm",
                "student_name",
                "student_cpf",
                "student_birthdate",
                "student_biological_sex",
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
        if profile != RegistrationProfile.OTHER:
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
        if profile == RegistrationProfile.HOLDER:
            groups.append(("holder_password", "holder_password_confirm", "aluno titular"))
            if include_dependent:
                groups.append(("dependent_password", "dependent_password_confirm", "dependente"))
        elif profile == RegistrationProfile.GUARDIAN:
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
        if profile == RegistrationProfile.HOLDER:
            self._resolve_class_group_collection("holder", required=self.catalog_is_available)
            if include_dependent:
                self._resolve_class_group_collection(
                    "dependent",
                    required=self.catalog_is_available,
                )
        elif profile == RegistrationProfile.GUARDIAN:
            self._resolve_class_group_collection("student", required=self.catalog_is_available)

        for index, dependent in enumerate(extra_dependents, start=1):
            if not dependent.get("biological_sex"):
                self.add_error(None, f"Dependente adicional {index}: informe o sexo biológico.")
            raw_group_ids = dependent.get("class_groups") or []
            if not self.catalog_is_available and not raw_group_ids:
                dependent["class_groups"] = []
                continue
            groups = resolve_class_groups(raw_group_ids)
            if self.catalog_is_available and not groups:
                self.add_error(None, f"Dependente adicional {index}: selecione ao menos uma turma.")
                continue
            if self._has_invalid_class_group_selection(raw_group_ids):
                self.add_error(
                    None,
                    f"Dependente adicional {index}: selecione apenas turmas válidas.",
                )
            self._add_class_group_eligibility_errors(
                None,
                groups,
                dependent.get("birth_date"),
                dependent.get("biological_sex", ""),
                f"Dependente adicional {index}",
            )
            dependent["class_groups"] = groups

    def _clean_plan_selection(self, profile, include_dependent, extra_dependents):
        plan_id = self.cleaned_data.get("selected_plan")
        if not plan_id:
            return
        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            self.add_error("selected_plan", "Selecione um plano válido.")
            return

        if plan.is_family_plan and not self._is_family_plan_allowed(
            profile,
            include_dependent,
            extra_dependents,
        ):
            self.add_error(
                "selected_plan",
                "Plano familiar disponível apenas para titular com dependente ou responsável com 2 crianças.",
            )
            return

        checkout_action = self.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
        expected_action = resolve_checkout_action_for_plan(plan)
        if checkout_action != CheckoutAction.PAY_LATER and checkout_action != expected_action:
            self.add_error(
                "checkout_action",
                "O meio de pagamento escolhido não corresponde ao plano selecionado.",
            )

    def _is_family_plan_allowed(self, profile, include_dependent, extra_dependents):
        if profile == RegistrationProfile.HOLDER:
            return bool(include_dependent)
        if profile == RegistrationProfile.GUARDIAN:
            return 1 + len(extra_dependents) >= 2
        return False

    def _resolve_class_group_collection(self, prefix, required):
        field_name = f"{prefix}_class_groups"
        raw_group_ids = self.cleaned_data.get(field_name) or []

        if not raw_group_ids and not required:
            self.cleaned_data[field_name] = []
            return

        if required and not self.catalog_is_available:
            self.cleaned_data[field_name] = []
            return

        groups = resolve_class_groups(raw_group_ids)

        if required and not groups:
            self.add_error(field_name, "Selecione ao menos uma turma.")
        if self._has_invalid_class_group_selection(raw_group_ids):
            self.add_error(field_name, "Selecione apenas turmas válidas.")

        self._add_class_group_eligibility_errors(
            field_name,
            groups,
            self.cleaned_data.get(f"{prefix}_birthdate"),
            self.cleaned_data.get(f"{prefix}_biological_sex", ""),
        )
        self.cleaned_data[field_name] = groups

    def _has_invalid_class_group_selection(self, raw_group_ids):
        for raw_group_id in raw_group_ids:
            if not str(raw_group_id):
                continue
            if resolve_class_groups([raw_group_id]):
                continue
            return True
        return False

    def _add_class_group_eligibility_errors(
        self,
        field_name,
        class_groups,
        birth_date,
        biological_sex,
        label_prefix=None,
    ):
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=birth_date,
                biological_sex=biological_sex,
                class_group=class_group,
            )
            if not error:
                continue
            message = f"{class_group.class_category.display_name} · {class_group.display_name}: {error}"
            if label_prefix:
                self.add_error(None, f"{label_prefix}: {message}")
            else:
                self.add_error(field_name, message)

    def _clean_kinship(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == RegistrationProfile.HOLDER and include_dependent:
            prefixes.append("dependent")
        if profile == RegistrationProfile.GUARDIAN:
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

    def _clean_martial_background(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == RegistrationProfile.HOLDER:
            prefixes.append("holder")
            if include_dependent:
                prefixes.append("dependent")
        elif profile == RegistrationProfile.GUARDIAN:
            prefixes.append("student")

        for prefix in prefixes:
            martial_art = self.cleaned_data.get(f"{prefix}_martial_art") or ""
            graduation = (self.cleaned_data.get(f"{prefix}_martial_art_graduation") or "").strip()
            belt = self.cleaned_data.get(f"{prefix}_jiu_jitsu_belt") or ""
            if martial_art and martial_art != MartialArt.JIU_JITSU and not graduation:
                self.add_error(
                    f"{prefix}_martial_art_graduation",
                    "Informe a graduação/nível na arte marcial.",
                )
            if martial_art == MartialArt.JIU_JITSU and not belt:
                self.add_error(
                    f"{prefix}_jiu_jitsu_belt",
                    "Informe a faixa de Jiu Jitsu.",
                )
            if martial_art != MartialArt.JIU_JITSU:
                self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None
            if not martial_art or martial_art == MartialArt.JIU_JITSU:
                self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""

        for index, dependent in enumerate(extra_dependents, start=1):
            martial_art = dependent.get("martial_art") or ""
            graduation = (dependent.get("martial_art_graduation") or "").strip()
            belt = dependent.get("jiu_jitsu_belt") or ""
            if martial_art and martial_art != MartialArt.JIU_JITSU and not graduation:
                self.add_error(None, f"Dependente adicional {index}: informe a graduação na arte marcial.")
            if martial_art == MartialArt.JIU_JITSU and not belt:
                self.add_error(None, f"Dependente adicional {index}: informe a faixa de Jiu Jitsu.")
            if martial_art != MartialArt.JIU_JITSU:
                dependent["jiu_jitsu_belt"] = ""
                dependent["jiu_jitsu_stripes"] = None
            if not martial_art or martial_art == MartialArt.JIU_JITSU:
                dependent["martial_art_graduation"] = ""

    def _clean_extra_dependents_payload(self):
        payload = parse_extra_dependents_payload(self.cleaned_data.get("extra_dependents_payload"))
        cleaned_dependents = []
        for index, dependent in enumerate(payload, start=1):
            birth_date_raw = dependent.get("birth_date") or ""
            birth_date = None
            jiu_jitsu_stripes = dependent.get("jiu_jitsu_stripes")
            if jiu_jitsu_stripes in ("", None):
                jiu_jitsu_stripes = None
            else:
                try:
                    jiu_jitsu_stripes = int(jiu_jitsu_stripes)
                except (TypeError, ValueError):
                    self.add_error(None, f"Dependente adicional {index}: graus de Jiu Jitsu inválidos.")
                    jiu_jitsu_stripes = None
                if jiu_jitsu_stripes is not None and not (0 <= jiu_jitsu_stripes <= 4):
                    self.add_error(None, f"Dependente adicional {index}: graus de Jiu Jitsu deve ser entre 0 e 4.")
                    jiu_jitsu_stripes = None
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
                    "biological_sex": dependent.get("biological_sex") or "",
                    "email": (dependent.get("email") or "").strip(),
                    "phone": (dependent.get("phone") or "").strip(),
                    "password": dependent.get("password") or "",
                    "password_confirm": dependent.get("password_confirm") or "",
                    "kinship_type": dependent.get("kinship_type") or "",
                    "kinship_other_label": (dependent.get("kinship_other_label") or "").strip(),
                    "class_groups": dependent.get("class_groups") or [],
                    "blood_type": dependent.get("blood_type") or "",
                    "allergies": dependent.get("allergies") or "",
                    "previous_injuries": dependent.get("injuries") or dependent.get("previous_injuries") or "",
                    "emergency_contact": dependent.get("emergency_contact") or "",
                    "martial_art": dependent.get("martial_art") or "",
                    "martial_art_graduation": dependent.get("martial_art_graduation") or "",
                    "jiu_jitsu_belt": dependent.get("jiu_jitsu_belt") or "",
                    "jiu_jitsu_stripes": jiu_jitsu_stripes,
                }
            )
        return cleaned_dependents
