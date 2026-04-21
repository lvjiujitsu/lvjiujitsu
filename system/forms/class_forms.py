from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory

from system.models import (
    ClassCategory,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    SpecialClass,
)
from system.constants import CLASS_STAFF_PERSON_TYPE_CODES, PersonTypeCode


class ClassGroupForm(forms.ModelForm):
    assistant_staff = forms.ModelMultipleChoiceField(
        queryset=Person.objects.none(),
        required=False,
        label="Equipe auxiliar",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = ClassGroup
        fields = (
            "code",
            "display_name",
            "class_category",
            "main_teacher",
            "description",
            "default_capacity",
            "is_active",
        )
        labels = {
            "code": "Código técnico",
            "display_name": "Nome base da turma",
            "class_category": "Categoria da turma",
            "main_teacher": "Professor principal",
            "description": "Descrição operacional",
            "default_capacity": "Capacidade padrão",
            "is_active": "Turma ativa",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["display_name"].help_text = (
            "Use o nome base da modalidade. Exemplo: Jiu Jitsu."
        )
        self.fields["class_category"].queryset = self._build_category_queryset()
        self.fields["main_teacher"].queryset = self._build_teacher_queryset()
        self.fields["assistant_staff"].queryset = self._build_assistant_queryset()
        self.fields["main_teacher"].empty_label = "Selecione"
        self.fields["default_capacity"].help_text = (
            "Capacidade de referência para matrículas e leitura operacional."
        )
        self.fields["assistant_staff"].help_text = (
            "Selecione quem também aparece vinculado à turma além do professor principal."
        )
        if not self.instance.pk and not self.initial.get("display_name"):
            self.initial["display_name"] = "Jiu Jitsu"
        if self.instance.pk:
            self.fields["assistant_staff"].initial = (
                self.instance.instructor_assignments.values_list("person_id", flat=True)
            )

    def clean(self):
        cleaned_data = super().clean()
        main_teacher = cleaned_data.get("main_teacher")
        assistant_staff = cleaned_data.get("assistant_staff")

        if cleaned_data.get("is_active") and not main_teacher:
            self.add_error(
                "main_teacher",
                "Selecione o professor principal da turma ativa.",
            )

        if main_teacher and assistant_staff and main_teacher in assistant_staff:
            self.add_error(
                "assistant_staff",
                "O professor principal não deve ser repetido na equipe auxiliar.",
            )

        return cleaned_data

    def save(self, commit=True):
        class_group = super().save(commit=commit)
        if commit:
            self.save_related(class_group)
        else:
            self._pending_assistant_staff = self.cleaned_data.get("assistant_staff")
        return class_group

    def save_m2m(self):
        super().save_m2m()
        if hasattr(self, "_pending_assistant_staff"):
            self.save_related(self.instance)

    def save_related(self, class_group):
        self._save_assistant_staff(class_group)

    def _save_assistant_staff(self, class_group):
        selected_people = list(self.cleaned_data.get("assistant_staff") or [])
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
                    "notes": "Vínculo auxiliar configurado pelo cadastro de turma.",
                },
            )

    def _build_category_queryset(self):
        current_category_id = getattr(self.instance, "class_category_id", None)
        return (
            ClassCategory.objects.filter(
                Q(is_active=True) | Q(pk=current_category_id),
            )
            .distinct()
            .order_by("display_order", "display_name")
        )

    def _build_teacher_queryset(self):
        current_teacher_id = getattr(self.instance, "main_teacher_id", None)
        return (
            Person.objects.filter(
                Q(person_type__code=PersonTypeCode.INSTRUCTOR, is_active=True)
                | Q(pk=current_teacher_id),
            )
            .distinct()
            .order_by("full_name")
        )

    def _build_assistant_queryset(self):
        current_ids = []
        if self.instance.pk:
            current_ids = list(
                self.instance.instructor_assignments.values_list("person_id", flat=True)
            )
        return (
            Person.objects.filter(
                Q(person_type__code__in=CLASS_STAFF_PERSON_TYPE_CODES, is_active=True)
                | Q(pk__in=current_ids),
            )
            .distinct()
            .order_by("full_name")
        )


class ClassGroupScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = (
            "weekday",
            "training_style",
            "start_time",
            "duration_minutes",
            "display_order",
            "is_active",
        )
        labels = {
            "weekday": "Dia",
            "training_style": "Estilo",
            "start_time": "Início",
            "duration_minutes": "Duração",
            "display_order": "Ordem",
            "is_active": "Ativo",
        }
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }


class BaseClassGroupScheduleFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_group = self._is_active_group()
        active_schedule_count = 0
        seen_slots = set()

        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                continue

            weekday = form.cleaned_data.get("weekday")
            training_style = form.cleaned_data.get("training_style")
            start_time = form.cleaned_data.get("start_time")
            duration_minutes = form.cleaned_data.get("duration_minutes")
            is_active = form.cleaned_data.get("is_active")
            has_values = any(
                value
                for value in (
                    weekday,
                    training_style,
                    start_time,
                    duration_minutes,
                    is_active,
                )
            )
            if not has_values:
                continue

            if weekday and training_style and start_time:
                slot_key = (weekday, training_style, start_time)
                if slot_key in seen_slots:
                    form.add_error(
                        "start_time",
                        "Já existe um horário igual vinculado a esta turma.",
                    )
                seen_slots.add(slot_key)

            if is_active:
                active_schedule_count += 1

        if active_group and active_schedule_count == 0:
            raise forms.ValidationError(
                "Cadastre ao menos um horário ativo para a turma ativa."
            )

    def _is_active_group(self):
        catalog_form = getattr(self, "catalog_form", None)
        if catalog_form is not None and hasattr(catalog_form, "cleaned_data"):
            return bool(catalog_form.cleaned_data.get("is_active"))
        return bool(getattr(self.instance, "is_active", False))


def get_class_group_schedule_formset(*, data=None, instance=None):
    target_instance = instance or ClassGroup()
    formset_class = inlineformset_factory(
        ClassGroup,
        ClassSchedule,
        form=ClassGroupScheduleForm,
        formset=BaseClassGroupScheduleFormSet,
        extra=1,
        can_delete=True,
    )
    return formset_class(
        data=data,
        instance=target_instance,
        prefix="schedules",
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
        current_group_id = getattr(self.instance, "class_group_id", None)
        self.fields["class_group"].queryset = (
            ClassGroup.objects.filter(Q(is_active=True) | Q(pk=current_group_id))
            .select_related("class_category", "main_teacher")
            .distinct()
            .order_by(
                "class_category__display_order",
                "class_category__display_name",
                "code",
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        class_group = cleaned_data.get("class_group")
        if cleaned_data.get("is_active") and class_group and not class_group.is_active:
            self.add_error(
                "class_group",
                "Ative a turma antes de ativar um horário vinculado a ela.",
            )
        return cleaned_data


class SpecialClassForm(forms.ModelForm):
    class Meta:
        model = SpecialClass
        fields = ("title", "date", "start_time", "duration_minutes", "teacher", "notes")
        labels = {
            "title": "Título",
            "date": "Data",
            "start_time": "Horário",
            "duration_minutes": "Duração (min)",
            "teacher": "Professor",
            "notes": "Observações",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = (
            Person.objects.filter(person_type__code=PersonTypeCode.INSTRUCTOR, is_active=True)
            .order_by("full_name")
        )
        self.fields["teacher"].required = False
        self.fields["notes"].required = False
        if not self.initial.get("title"):
            self.initial["title"] = settings.SPECIAL_CLASS_DEFAULT_TITLE
