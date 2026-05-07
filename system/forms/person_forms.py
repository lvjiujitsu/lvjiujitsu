from django import forms

from system.models import (
    BiologicalSex,
    BloodType,
    ClassCategory,
    JiuJitsuBelt,
    MartialArt,
    Person,
    PersonType,
)
from system.models.class_membership import get_class_group_eligibility_error
from system.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES
from system.services.class_overview import (
    build_class_group_filter_value,
    get_class_group_filter_choices,
    get_public_class_group_choice_options,
    get_weekday_filter_choices,
    resolve_class_group_selection,
)
from system.services.registration import sync_person_class_enrollments
from system.services.payroll_rules import (
    PayrollRuleError,
    get_payroll_form_initial,
    save_person_payroll_config,
)
from system.utils import ensure_formatted_cpf
from system.constants import CLASS_STAFF_PERSON_TYPE_CODES


class PersonTypeForm(forms.ModelForm):
    class Meta:
        model = PersonType
        fields = ("code", "display_name", "description", "is_active")
        labels = {
            "code": "Código técnico",
            "display_name": "Nome exibido",
            "description": "Descrição",
            "is_active": "Ativo",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class PersonListFilterForm(forms.Form):
    full_name = forms.CharField(required=False, label="Nome")
    cpf = forms.CharField(required=False, label="CPF")
    is_teacher = forms.BooleanField(required=False, label="Somente professores")
    class_category = forms.ModelChoiceField(
        queryset=ClassCategory.objects.none(),
        required=False,
        label="Categoria",
        empty_label="Todas",
    )
    class_group_key = forms.ChoiceField(required=False, label="Turma")
    weekday = forms.ChoiceField(required=False, label="Horário")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")
        self.fields["class_group_key"].choices = [("", "Todas")] + get_class_group_filter_choices()
        self.fields["weekday"].choices = [("", "Todos")] + get_weekday_filter_choices()


class PersonForm(forms.ModelForm):
    main_field_names = (
        "full_name",
        "cpf",
        "email",
        "phone",
        "birth_date",
        "biological_sex",
        "blood_type",
        "allergies",
        "previous_injuries",
        "emergency_contact",
        "martial_art",
        "martial_art_graduation",
        "jiu_jitsu_belt",
        "jiu_jitsu_stripes",
        "person_type",
        "class_groups",
        "is_active",
    )
    payroll_field_names = (
        "payroll_enabled",
        "payroll_payment_day",
        "payroll_fixed_monthly",
        "payroll_per_student_amount",
        "payroll_student_percentage",
        "payroll_per_class_amount",
        "payroll_rules_json",
    )
    person_type = forms.ModelChoiceField(
        queryset=PersonType.objects.none(),
        required=True,
        label="Tipo de vínculo",
    )
    class_groups = forms.MultipleChoiceField(
        required=False,
        label="Turmas liberadas",
        help_text="Selecione as turmas que a pessoa pode frequentar. Os horários ativos dessas turmas ficam liberados automaticamente.",
        widget=forms.CheckboxSelectMultiple,
    )
    payroll_enabled = forms.BooleanField(
        required=False,
        label="Repasse ativo",
    )
    payroll_payment_day = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=28,
        label="Dia do pagamento",
    )
    payroll_fixed_monthly = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Valor fixo mensal",
    )
    payroll_per_student_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Valor por aluno",
    )
    payroll_student_percentage = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        max_digits=5,
        decimal_places=2,
        label="Percentual por aluno",
    )
    payroll_per_class_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Valor por aluno/aula",
    )
    payroll_rules_json = forms.CharField(
        required=False,
        label="Regras avançadas",
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    class Meta:
        model = Person
        fields = (
            "full_name",
            "cpf",
            "email",
            "phone",
            "birth_date",
            "biological_sex",
            "blood_type",
            "allergies",
            "previous_injuries",
            "emergency_contact",
            "martial_art",
            "martial_art_graduation",
            "jiu_jitsu_belt",
            "jiu_jitsu_stripes",
            "person_type",
            "is_active",
        )
        labels = {
            "full_name": "Nome completo",
            "cpf": "CPF",
            "email": "E-mail",
            "phone": "Telefone",
            "birth_date": "Data de nascimento",
            "biological_sex": "Sexo biológico",
            "blood_type": "Tipo sanguíneo",
            "allergies": "Alergias",
            "previous_injuries": "Lesões prévias",
            "emergency_contact": "Contato de emergência",
            "martial_art": "Modalidade já praticada",
            "martial_art_graduation": "Graduação/nível na modalidade",
            "jiu_jitsu_belt": "Faixa de Jiu Jitsu",
            "jiu_jitsu_stripes": "Graus na faixa (0 a 4)",
            "is_active": "Cadastro ativo",
        }
        widgets = {
            "birth_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "biological_sex": forms.Select(
                choices=[("", "Selecione")] + list(BiologicalSex.choices),
            ),
            "blood_type": forms.Select(
                choices=[("", "Selecione")] + list(BloodType.choices),
            ),
            "allergies": forms.Textarea(attrs={"rows": 3}),
            "previous_injuries": forms.Textarea(attrs={"rows": 3}),
            "emergency_contact": forms.TextInput(
                attrs={"placeholder": "Nome e telefone do contato"}
            ),
            "martial_art": forms.Select(
                choices=[("", "Não possui")] + list(MartialArt.choices),
            ),
            "jiu_jitsu_belt": forms.Select(
                choices=[("", "Selecione")] + list(JiuJitsuBelt.choices),
            ),
        }

    def __init__(self, *args, **kwargs):
        person_type_codes = kwargs.pop("person_type_codes", None)
        self.show_payroll_fields = kwargs.pop("show_payroll_fields", True)
        super().__init__(*args, **kwargs)
        person_type_queryset = PersonType.objects.filter(
            is_active=True
        )
        if person_type_codes:
            person_type_queryset = person_type_queryset.filter(code__in=person_type_codes)
        self.fields["person_type"].queryset = person_type_queryset.order_by("display_name")
        self.fields["class_groups"].choices = get_public_class_group_choice_options()
        if self.instance.pk:
            self.initial["birth_date"] = (
                self.instance.birth_date.strftime("%Y-%m-%d")
                if self.instance.birth_date
                else ""
            )
            self.fields["class_groups"].initial = _get_initial_class_group_values(
                self.instance
            )
            payroll_initial = get_payroll_form_initial(self.instance)
            for field_name, value in payroll_initial.items():
                self.fields[field_name].initial = value
        else:
            self.fields["payroll_payment_day"].initial = 28
        self.order_fields(
            [
                "full_name",
                "cpf",
                "email",
                "phone",
                "birth_date",
                "biological_sex",
                "blood_type",
                "allergies",
                "previous_injuries",
                "emergency_contact",
                "martial_art",
                "martial_art_graduation",
                "jiu_jitsu_belt",
                "jiu_jitsu_stripes",
                "person_type",
                "class_groups",
                "is_active",
                "payroll_enabled",
                "payroll_payment_day",
                "payroll_fixed_monthly",
                "payroll_per_student_amount",
                "payroll_student_percentage",
                "payroll_per_class_amount",
                "payroll_rules_json",
            ]
        )

    @property
    def main_fields(self):
        return [self[name] for name in self.main_field_names]

    @property
    def payroll_fields(self):
        if not self.show_payroll_fields:
            return []
        return [self[name] for name in self.payroll_field_names]

    def clean_cpf(self):
        return ensure_formatted_cpf(self.cleaned_data.get("cpf", ""))

    def clean(self):
        cleaned_data = super().clean()
        martial_art = cleaned_data.get("martial_art") or ""
        graduation = (cleaned_data.get("martial_art_graduation") or "").strip()
        jiu_jitsu_belt = cleaned_data.get("jiu_jitsu_belt") or ""

        if martial_art and not graduation:
            self.add_error("martial_art_graduation", "Informe a graduação/nível na arte marcial.")
        if martial_art == MartialArt.JIU_JITSU and not jiu_jitsu_belt:
            self.add_error("jiu_jitsu_belt", "Informe a faixa atual de Jiu Jitsu.")
        if martial_art != MartialArt.JIU_JITSU:
            cleaned_data["jiu_jitsu_belt"] = ""
            cleaned_data["jiu_jitsu_stripes"] = None

        class_group_values = cleaned_data.get("class_groups") or []
        class_groups = resolve_class_group_selection(class_group_values)
        person_type = cleaned_data.get("person_type")
        if class_groups and not (
            person_type and person_type.code in CLASS_ENROLLMENT_PERSON_TYPE_CODES
        ):
            self.add_error(
                "class_groups",
                "Apenas aluno titular ou dependente pode receber turmas liberadas.",
            )
        seen_errors = set()
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=cleaned_data.get("birth_date"),
                biological_sex=cleaned_data.get("biological_sex", ""),
                class_group=class_group,
            )
            if error:
                message = (
                    f"{class_group.class_category.display_name} · {class_group.display_name}: {error}"
                )
                if message in seen_errors:
                    continue
                self.add_error(
                    "class_groups",
                    message,
                )
                seen_errors.add(message)
        cleaned_data["class_groups"] = class_groups
        self._clean_payroll_config(cleaned_data)
        return cleaned_data

    def save(self, commit=True):
        person = super().save(commit=False)
        class_groups = list(self.cleaned_data.get("class_groups") or [])
        primary_group = class_groups[0] if class_groups else None
        person.class_group = primary_group
        person.class_category = primary_group.class_category if primary_group else None
        person.class_schedule = None
        if commit:
            person.save()
            sync_person_class_enrollments(person, class_groups)
            try:
                save_person_payroll_config(person, self.cleaned_data)
            except PayrollRuleError as exc:
                raise ValueError(str(exc)) from exc
        return person

    def _clean_payroll_config(self, cleaned_data):
        person_type = cleaned_data.get("person_type")
        payroll_enabled = bool(cleaned_data.get("payroll_enabled"))
        has_payroll_values = any(
            cleaned_data.get(field_name)
            for field_name in (
                "payroll_fixed_monthly",
                "payroll_per_student_amount",
                "payroll_student_percentage",
                "payroll_per_class_amount",
                "payroll_rules_json",
            )
        )
        is_staff = bool(
            person_type and person_type.code in CLASS_STAFF_PERSON_TYPE_CODES
        )
        if (payroll_enabled or has_payroll_values) and not is_staff:
            self.add_error(
                "payroll_enabled",
                "Repasse permitido apenas para Professor ou Administrativo.",
            )
            return
        if not payroll_enabled:
            return
        if not cleaned_data.get("payroll_payment_day"):
            cleaned_data["payroll_payment_day"] = 28
        try:
            from system.services.payroll_rules import build_payroll_payload_from_form

            build_payroll_payload_from_form(cleaned_data)
        except PayrollRuleError as exc:
            self.add_error("payroll_rules_json", str(exc))


def _get_initial_class_group_values(person):
    logical_values = []
    seen_values = set()
    active_groups = (
        person.class_enrollments.select_related("class_group", "class_group__class_category")
        .filter(status="active")
        .order_by(
            "class_group__class_category__display_order",
            "class_group__class_category__display_name",
            "class_group__display_name",
            "class_group__code",
        )
    )
    for enrollment in active_groups:
        class_group = enrollment.class_group
        filter_value = build_class_group_filter_value(
            class_group.class_category_id,
            class_group.display_name,
        )
        if filter_value in seen_values:
            continue
        logical_values.append(filter_value)
        seen_values.add(filter_value)
    return logical_values
