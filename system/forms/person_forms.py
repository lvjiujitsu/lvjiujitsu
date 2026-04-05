from django import forms

from system.models import BiologicalSex, BloodType, ClassGroup, Person, PersonType
from system.models.class_membership import get_class_group_eligibility_error
from system.services.registration import sync_person_class_enrollments
from system.utils import ensure_formatted_cpf


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


class PersonForm(forms.ModelForm):
    person_type = forms.ModelChoiceField(
        queryset=PersonType.objects.none(),
        required=True,
        label="Tipo de vínculo",
    )
    class_groups = forms.ModelMultipleChoiceField(
        queryset=ClassGroup.objects.none(),
        required=False,
        label="Turmas liberadas",
        help_text="Selecione as turmas que a pessoa pode frequentar. Os horários ativos dessas turmas ficam liberados automaticamente.",
        widget=forms.CheckboxSelectMultiple,
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
            "is_active": "Cadastro ativo",
        }
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person_type"].queryset = PersonType.objects.filter(
            is_active=True
        ).order_by("display_name")
        self.fields["class_groups"].queryset = ClassGroup.objects.filter(
            is_active=True
        ).select_related("class_category", "main_teacher").order_by(
            "class_category__display_order",
            "class_category__display_name",
            "code",
        )
        if self.instance.pk:
            self.fields["class_groups"].initial = list(
                self.instance.class_enrollments.select_related("class_group")
                .filter(status="active")
                .values_list("class_group_id", flat=True)
            )
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
                "person_type",
                "class_groups",
                "is_active",
            ]
        )

    def clean_cpf(self):
        return ensure_formatted_cpf(self.cleaned_data.get("cpf", ""))

    def clean(self):
        cleaned_data = super().clean()
        class_groups = cleaned_data.get("class_groups") or []
        person_type = cleaned_data.get("person_type")
        if class_groups and not (person_type and person_type.code in ("student", "dependent")):
            self.add_error(
                "class_groups",
                "Apenas aluno titular ou dependente pode receber turmas liberadas.",
            )
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=cleaned_data.get("birth_date"),
                biological_sex=cleaned_data.get("biological_sex", ""),
                class_group=class_group,
            )
            if error:
                self.add_error(
                    "class_groups",
                    f"{class_group.class_category.display_name} · {class_group.display_name}: {error}",
                )
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
        return person
