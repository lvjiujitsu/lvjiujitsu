from django import forms

from system.models import ClassGroup, GraduationExamParticipation, GraduationRule, IbjjfBelt


class GraduationRuleForm(forms.ModelForm):
    class Meta:
        model = GraduationRule
        fields = (
            "scope",
            "discipline",
            "current_belt",
            "current_degree",
            "target_belt",
            "target_degree",
            "minimum_active_days",
            "minimum_attendances",
            "minimum_age",
            "maximum_inactivity_days",
            "requires_exam",
            "criteria_notes",
            "is_active",
        )


class GraduationPanelFilterForm(forms.Form):
    class_group = forms.ModelChoiceField(label="Turma", queryset=ClassGroup.objects.none(), required=False)
    belt_rank = forms.ModelChoiceField(label="Faixa atual", queryset=IbjjfBelt.objects.none(), required=False)
    eligible_only = forms.BooleanField(label="Mostrar somente aptos", required=False, initial=True)

    def __init__(self, *args, class_group_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_group"].queryset = class_group_queryset or ClassGroup.objects.none()
        self.fields["belt_rank"].queryset = IbjjfBelt.objects.filter(is_active=True).order_by("display_order")


class GraduationExamCreateForm(forms.Form):
    title = forms.CharField(label="Avaliacao", max_length=255)
    scheduled_for = forms.DateField(label="Data do exame")
    notes = forms.CharField(label="Observacoes", required=False, widget=forms.Textarea)


class GraduationParticipationDecisionForm(forms.Form):
    status = forms.ChoiceField(label="Decisao", choices=GraduationExamParticipation.STATUS_CHOICES)
    target_belt = forms.ModelChoiceField(label="Faixa de destino", queryset=IbjjfBelt.objects.none(), required=False)
    target_degree = forms.IntegerField(label="Grau de destino", min_value=0, max_value=4, required=False)
    decision_notes = forms.CharField(label="Observacoes", required=False, widget=forms.Textarea)
    promotion_date = forms.DateField(label="Data da promocao", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_belt"].queryset = IbjjfBelt.objects.filter(is_active=True).order_by("display_order")
