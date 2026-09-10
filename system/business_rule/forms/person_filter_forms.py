from django import forms
from system.business_rule.models import ClassCategory, JiuJitsuBelt, PersonType
from system.business_rule.services.class_overview import (
    get_class_group_filter_choices,
    get_weekday_filter_choices,
)


class PersonListFilterForm(forms.Form):
    full_name = forms.CharField(required=False, label="Nome")
    cpf = forms.CharField(required=False, label="CPF")
    is_teacher = forms.BooleanField(required=False, label="Somente professores")
    person_type = forms.ModelChoiceField(
        queryset=PersonType.objects.none(),
        required=False,
        label="Tipo",
        empty_label="Todos",
    )
    jiu_jitsu_belt = forms.ChoiceField(required=False, label="Faixa")
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
        self.fields["person_type"].queryset = PersonType.objects.filter(
            is_active=True
        ).order_by("display_name")
        self.fields["jiu_jitsu_belt"].choices = [("", "Todas")] + list(JiuJitsuBelt.choices)
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")
        self.fields["class_group_key"].choices = [("", "Todas")] + get_class_group_filter_choices()
        self.fields["weekday"].choices = [("", "Todos")] + get_weekday_filter_choices()
