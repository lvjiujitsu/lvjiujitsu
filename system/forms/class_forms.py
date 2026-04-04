from django import forms

from system.models import (
    ClassCategory,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
)


class ClassGroupForm(forms.ModelForm):
    assistant_staff = forms.ModelMultipleChoiceField(
        queryset=Person.objects.none(),
        required=False,
        label="Instrutores auxiliares",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ClassGroup
        fields = (
            "code",
            "display_name",
            "audience",
            "class_category",
            "main_teacher",
            "description",
            "default_capacity",
            "is_public",
            "is_active",
        )
        labels = {
            "code": "Código técnico",
            "display_name": "Nome base da turma",
            "audience": "Público",
            "class_category": "Categoria da turma",
            "main_teacher": "Professor principal",
            "description": "Descrição",
            "default_capacity": "Capacidade padrão",
            "is_public": "Exibir em Informações",
            "is_active": "Turma ativa",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["display_name"].help_text = (
            "Use apenas o nome da modalidade. Exemplo: Jiu Jitsu."
        )
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")
        self.fields["main_teacher"].queryset = Person.objects.filter(
            person_types__code="instructor",
            is_active=True,
        ).distinct().order_by("full_name")
        self.fields["assistant_staff"].queryset = Person.objects.filter(
            person_types__code__in=("administrative-assistant", "instructor"),
            is_active=True,
        ).distinct().order_by("full_name")
        if not self.instance.pk and not self.initial.get("display_name"):
            self.initial["display_name"] = "Jiu Jitsu"
        if self.instance.pk:
            self.fields["assistant_staff"].initial = self.instance.instructor_assignments.values_list(
                "person_id",
                flat=True,
            )

    def clean(self):
        cleaned_data = super().clean()
        main_teacher = cleaned_data.get("main_teacher")
        assistant_staff = cleaned_data.get("assistant_staff")

        if main_teacher and assistant_staff and main_teacher in assistant_staff:
            self.add_error(
                "assistant_staff",
                "O professor principal não deve ser repetido como instrutor auxiliar.",
            )

        return cleaned_data

    def save(self, commit=True):
        class_group = super().save(commit=commit)
        if commit:
            self._save_assistant_staff(class_group)
        else:
            self._pending_assistant_staff = self.cleaned_data.get("assistant_staff")
        return class_group

    def save_m2m(self):
        super().save_m2m()
        if hasattr(self, "_pending_assistant_staff"):
            self._save_assistant_staff(self.instance)

    def _save_assistant_staff(self, class_group):
        selected_people = self.cleaned_data.get("assistant_staff") or []
        selected_ids = {person.id for person in selected_people}

        ClassInstructorAssignment.objects.filter(class_group=class_group).exclude(
            person_id__in=selected_ids
        ).delete()

        for person in selected_people:
            ClassInstructorAssignment.objects.update_or_create(
                class_group=class_group,
                person=person,
                defaults={
                    "is_primary": False,
                    "notes": "Vínculo auxiliar configurado pelo CRUD de turma.",
                },
            )


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = (
            "class_group",
            "weekday",
            "training_style",
            "start_time",
            "duration_minutes",
            "display_order",
            "is_active",
        )
        labels = {
            "class_group": "Turma",
            "weekday": "Dia da semana",
            "training_style": "Estilo de treino",
            "start_time": "Horário de início",
            "duration_minutes": "Duração (minutos)",
            "display_order": "Ordem de exibição",
            "is_active": "Horário ativo",
        }
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_group"].queryset = ClassGroup.objects.filter(
            is_active=True
        ).select_related("class_category", "main_teacher").order_by("audience", "code")
