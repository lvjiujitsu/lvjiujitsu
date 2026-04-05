from django import forms

from system.models import BloodType, ClassCategory, ClassGroup, ClassSchedule, Person, PersonType
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
    class_category = forms.ModelChoiceField(
        queryset=ClassCategory.objects.none(),
        required=False,
        label="Categoria da pessoa",
    )
    class_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.none(),
        required=False,
        label="Turma vinculada",
    )
    class_schedule = forms.ModelChoiceField(
        queryset=ClassSchedule.objects.none(),
        required=False,
        label="Horário vinculado",
    )

    class Meta:
        model = Person
        fields = (
            "full_name",
            "cpf",
            "email",
            "phone",
            "birth_date",
            "blood_type",
            "allergies",
            "previous_injuries",
            "emergency_contact",
            "person_type",
            "class_category",
            "class_group",
            "class_schedule",
            "is_active",
        )
        labels = {
            "full_name": "Nome completo",
            "cpf": "CPF",
            "email": "E-mail",
            "phone": "Telefone",
            "birth_date": "Data de nascimento",
            "blood_type": "Tipo sanguíneo",
            "allergies": "Alergias",
            "previous_injuries": "Lesões prévias",
            "emergency_contact": "Contato de emergência",
            "is_active": "Cadastro ativo",
        }
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
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
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")
        self.fields["class_group"].queryset = ClassGroup.objects.filter(
            is_active=True
        ).select_related("class_category", "main_teacher").order_by(
            "class_category__display_order",
            "class_category__display_name",
            "code",
        )
        self.fields["class_schedule"].queryset = ClassSchedule.objects.filter(
            is_active=True
        ).select_related("class_group").order_by(
            "class_group__display_name",
            "display_order",
            "start_time",
        )

    def clean_cpf(self):
        return ensure_formatted_cpf(self.cleaned_data.get("cpf", ""))

    def clean(self):
        cleaned_data = super().clean()
        class_category = cleaned_data.get("class_category")
        class_group = cleaned_data.get("class_group")
        class_schedule = cleaned_data.get("class_schedule")

        if class_group:
            cleaned_data["class_category"] = class_group.class_category
            class_category = class_group.class_category

        if class_category and class_group and class_group.class_category_id != class_category.id:
            self.add_error("class_group", "A turma precisa pertencer à categoria selecionada.")

        if class_schedule and class_group and class_schedule.class_group_id != class_group.id:
            self.add_error(
                "class_schedule",
                "O horário selecionado não pertence à turma escolhida.",
            )

        return cleaned_data
