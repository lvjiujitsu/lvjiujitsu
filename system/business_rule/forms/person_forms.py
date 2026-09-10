from django import forms
from system.business_rule.models import (
    BiologicalSex,
    BloodType,
    ClassGroup,
    JiuJitsuBelt,
    MartialArt,
    OperationalRole,
    Person,
    PersonType,
)
from system.business_rule.models.class_membership import get_class_group_eligibility_error
from system.business_rule.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES, OperationalRoleCode
from system.business_rule.services.class_overview import (
    build_class_group_filter_value,
    get_public_class_group_choice_options,
    resolve_class_group_selection,
)
from system.business_rule.services.operational_roles import sync_person_operational_roles
from system.business_rule.services.registration import sync_person_class_enrollments
from system.business_rule.services.payroll_rules import (
    PayrollRuleError,
    get_payroll_form_initial,
    save_person_payroll_config,
)
from system.core.documents import ensure_formatted_cpf
from system.business_rule.forms.person_field_groups import PersonFieldGroupsMixin
from system.business_rule.forms.person_martial_art_history import PersonMartialArtMixin
from system.business_rule.forms.person_operational_roles import PersonOperationalRolesMixin
from system.business_rule.forms.person_payroll_fields import PersonPayrollMixin


MARTIAL_ART_EXPERIENCE_YES = "yes"


MARTIAL_ART_EXPERIENCE_NO = "no"


MARTIAL_ART_EXPERIENCE_CHOICES = [
    ("", "Selecione"),
    (MARTIAL_ART_EXPERIENCE_YES, "Sim"),
    (MARTIAL_ART_EXPERIENCE_NO, "Não"),
]


class PersonForm(
    PersonFieldGroupsMixin,
    PersonMartialArtMixin,
    PersonOperationalRolesMixin,
    PersonPayrollMixin,
    forms.ModelForm,
):
    address_field_names = (
        "postal_code",
        "address",
        "address_number",
        "address_complement",
        "address_neighborhood",
        "city",
    )
    identity_field_names = (
        "full_name",
        "cpf",
        "email",
        "phone",
        "birth_date",
        "biological_sex",
    )
    health_field_names = (
        "blood_type",
        "allergies",
        "previous_injuries",
        "emergency_contact",
    )
    martial_art_field_names = (
        "has_martial_art",
        "martial_art",
        "martial_art_graduation",
        "jiu_jitsu_belt",
        "jiu_jitsu_stripes",
        "martial_art_started_at",
        "martial_art_last_graduation_at",
        "previous_academy",
    )
    relationship_field_names = (
        "person_type",
        "class_groups",
        "is_active",
    )
    operational_role_field_names = (
        "operational_roles",
        "class_assistant_group",
    )
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
        "has_martial_art",
        "martial_art",
        "martial_art_graduation",
        "jiu_jitsu_belt",
        "jiu_jitsu_stripes",
        "martial_art_started_at",
        "martial_art_last_graduation_at",
        "previous_academy",
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
    has_martial_art = forms.ChoiceField(
        required=False,
        choices=MARTIAL_ART_EXPERIENCE_CHOICES,
        label="Já praticou arte marcial?",
    )
    class_groups = forms.MultipleChoiceField(
        required=False,
        label="Turmas liberadas",
        help_text="Selecione as turmas que a pessoa pode frequentar. Os horários ativos dessas turmas ficam liberados automaticamente.",
        widget=forms.CheckboxSelectMultiple,
    )
    operational_roles = forms.ModelMultipleChoiceField(
        queryset=OperationalRole.objects.none(),
        required=False,
        label="Papéis operacionais",
        help_text="Funções acumuláveis desta pessoa (apoio de turma, gestão etc.), além do tipo de vínculo.",
        widget=forms.CheckboxSelectMultiple,
    )
    class_assistant_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.none(),
        required=False,
        label="Turma do apoio",
        help_text="Obrigatório quando o papel \"Apoio de turma\" estiver selecionado.",
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
            "postal_code",
            "address",
            "address_number",
            "address_complement",
            "address_neighborhood",
            "city",
            "blood_type",
            "allergies",
            "previous_injuries",
            "emergency_contact",
            "martial_art",
            "martial_art_graduation",
            "jiu_jitsu_belt",
            "jiu_jitsu_stripes",
            "martial_art_started_at",
            "martial_art_last_graduation_at",
            "previous_academy",
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
            "postal_code": "CEP",
            "address": "Logradouro",
            "address_number": "Número",
            "address_complement": "Complemento",
            "address_neighborhood": "Bairro",
            "city": "Cidade",
            "blood_type": "Tipo sanguíneo",
            "allergies": "Alergias",
            "previous_injuries": "Lesões prévias",
            "emergency_contact": "Contato de emergência",
            "martial_art": "Modalidade já praticada",
            "martial_art_graduation": "Graduação/nível na modalidade",
            "jiu_jitsu_belt": "Faixa de Jiu Jitsu",
            "jiu_jitsu_stripes": "Graus na faixa (0 a 4)",
            "martial_art_started_at": "Início no jiu jitsu",
            "martial_art_last_graduation_at": "Última graduação anterior",
            "previous_academy": "Academia anterior",
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
            "martial_art_started_at": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "martial_art_last_graduation_at": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }

    def __init__(self, *args, **kwargs):
        person_type_codes = kwargs.pop("person_type_codes", None)
        self.show_payroll_fields = kwargs.pop("show_payroll_fields", True)
        self.show_operational_role_fields = kwargs.pop("show_operational_role_fields", True)
        super().__init__(*args, **kwargs)
        self.fields["has_martial_art"].widget.attrs.update(
            {"data-martial-art-presence-select": "person"}
        )
        for field_name in self._martial_art_detail_field_names():
            self.fields[field_name].widget.attrs.update(
                {"data-martial-art-detail-field": "person"}
            )
        person_type_queryset = PersonType.objects.filter(
            is_active=True
        )
        if person_type_codes:
            person_type_queryset = person_type_queryset.filter(code__in=person_type_codes)
        self.fields["person_type"].queryset = person_type_queryset.order_by("display_name")
        self.fields["class_groups"].choices = get_public_class_group_choice_options()
        self.fields["operational_roles"].queryset = OperationalRole.objects.filter(
            is_active=True
        ).order_by("display_name")
        self.fields["class_assistant_group"].queryset = ClassGroup.objects.filter(
            is_active=True
        ).order_by("class_category__display_order", "display_name")
        if self.instance.pk:
            active_assignments = list(
                self.instance.operational_role_assignments.filter(is_active=True)
            )
            self.fields["operational_roles"].initial = [
                assignment.role_id for assignment in active_assignments
            ]
            class_assistant_assignment = next(
                (
                    assignment
                    for assignment in active_assignments
                    if assignment.role.code == OperationalRoleCode.CLASS_ASSISTANT
                    and assignment.class_group_id
                ),
                None,
            )
            if class_assistant_assignment:
                self.fields["class_assistant_group"].initial = (
                    class_assistant_assignment.class_group_id
                )
        if self.instance.pk:
            self.initial["has_martial_art"] = (
                MARTIAL_ART_EXPERIENCE_YES
                if _person_has_martial_art_history(self.instance)
                else MARTIAL_ART_EXPERIENCE_NO
            )
            self.initial["birth_date"] = (
                self.instance.birth_date.strftime("%Y-%m-%d")
                if self.instance.birth_date
                else ""
            )
            self.initial["martial_art_started_at"] = (
                self.instance.martial_art_started_at.strftime("%Y-%m-%d")
                if self.instance.martial_art_started_at
                else ""
            )
            self.initial["martial_art_last_graduation_at"] = (
                self.instance.martial_art_last_graduation_at.strftime("%Y-%m-%d")
                if self.instance.martial_art_last_graduation_at
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
                "postal_code",
                "address",
                "address_number",
                "address_complement",
                "address_neighborhood",
                "city",
                "blood_type",
                "allergies",
                "previous_injuries",
                "emergency_contact",
                "has_martial_art",
                "martial_art",
                "martial_art_graduation",
                "jiu_jitsu_belt",
                "jiu_jitsu_stripes",
                "martial_art_started_at",
                "martial_art_last_graduation_at",
                "previous_academy",
                "person_type",
                "class_groups",
                "operational_roles",
                "class_assistant_group",
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

    def clean_cpf(self):
        try:
            return ensure_formatted_cpf(self.cleaned_data.get("cpf", ""))
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error

    def clean(self):
        cleaned_data = super().clean()
        martial_art = cleaned_data.get("martial_art") or ""
        has_martial_art = cleaned_data.get("has_martial_art") or ""
        graduation = (cleaned_data.get("martial_art_graduation") or "").strip()
        jiu_jitsu_belt = cleaned_data.get("jiu_jitsu_belt") or ""

        if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
            self._clear_martial_art_history(cleaned_data)
            martial_art = ""
            graduation = ""
            jiu_jitsu_belt = ""
        elif not martial_art:
            self.add_error("martial_art", "Selecione a arte marcial praticada.")
        if martial_art and martial_art != MartialArt.JIU_JITSU and not graduation:
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
        self._clean_operational_roles(cleaned_data)
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
            if self.show_operational_role_fields:
                selected_roles = self.cleaned_data.get("operational_roles") or []
                sync_person_operational_roles(
                    person,
                    [role.pk for role in selected_roles],
                    class_assistant_group=self.cleaned_data.get("class_assistant_group"),
                )
        return person


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
            "class_group__main_teacher__full_name",
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


def _person_has_martial_art_history(person):
    return any(
        (
            person.martial_art,
            person.martial_art_graduation,
            person.jiu_jitsu_belt,
            person.jiu_jitsu_stripes is not None,
            person.martial_art_started_at,
            person.martial_art_last_graduation_at,
            person.previous_academy,
        )
    )
