from django import forms
from django.db.models import Q

from system.constants import PersonTypeCode
from system.models import BeltRank, Graduation, GraduationRule, Person


class BeltRankForm(forms.ModelForm):
    class Meta:
        model = BeltRank
        fields = (
            "code",
            "display_name",
            "audience",
            "color_hex",
            "tip_color_hex",
            "stripe_color_hex",
            "max_grades",
            "min_age",
            "max_age",
            "next_rank",
            "display_order",
            "is_active",
        )
        labels = {
            "code": "Código técnico",
            "display_name": "Nome da faixa",
            "audience": "Público",
            "color_hex": "Cor do corpo",
            "tip_color_hex": "Cor da ponteira",
            "stripe_color_hex": "Cor das listras",
            "max_grades": "Graus máximos",
            "min_age": "Idade mínima",
            "max_age": "Idade máxima",
            "next_rank": "Próxima faixa",
            "display_order": "Ordem de exibição",
            "is_active": "Ativa",
        }
        widgets = {
            "color_hex": forms.TextInput(attrs={"type": "color"}),
            "tip_color_hex": forms.TextInput(attrs={"type": "color"}),
            "stripe_color_hex": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_id = getattr(self.instance, "pk", None)
        queryset = BeltRank.objects.all()
        if current_id is not None:
            queryset = queryset.exclude(pk=current_id)
        self.fields["next_rank"].queryset = queryset.order_by("display_order", "display_name")
        self.fields["next_rank"].required = False
        self.fields["next_rank"].empty_label = "Selecione (opcional)"

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get("min_age")
        max_age = cleaned_data.get("max_age")
        if min_age is not None and max_age is not None and max_age < min_age:
            self.add_error("max_age", "Idade máxima deve ser maior ou igual à mínima.")
        return cleaned_data


class GraduationRuleForm(forms.ModelForm):
    class Meta:
        model = GraduationRule
        fields = (
            "belt_rank",
            "from_grade",
            "to_grade",
            "min_months_in_current_grade",
            "min_classes_required",
            "min_classes_window_months",
            "notes",
            "is_active",
        )
        labels = {
            "belt_rank": "Faixa",
            "from_grade": "Grau de origem",
            "to_grade": "Grau de destino (vazio = próxima faixa)",
            "min_months_in_current_grade": "Meses mínimos no grau atual",
            "min_classes_required": "Mínimo de aulas aprovadas",
            "min_classes_window_months": "Janela de aulas (meses)",
            "notes": "Observações",
            "is_active": "Ativa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["belt_rank"].queryset = BeltRank.objects.order_by("display_order", "display_name")
        self.fields["to_grade"].required = False

    def clean(self):
        cleaned_data = super().clean()
        belt_rank = cleaned_data.get("belt_rank")
        from_grade = cleaned_data.get("from_grade")
        to_grade = cleaned_data.get("to_grade")
        if belt_rank and from_grade is not None and from_grade > belt_rank.max_grades:
            self.add_error("from_grade", "Grau de origem maior que o máximo da faixa.")
        if to_grade is not None and belt_rank and to_grade > belt_rank.max_grades:
            self.add_error("to_grade", "Grau de destino maior que o máximo da faixa.")
        if to_grade is not None and from_grade is not None and to_grade <= from_grade:
            self.add_error("to_grade", "Grau de destino deve ser maior que o de origem.")
        if to_grade is None and belt_rank and belt_rank.next_rank_id is None:
            self.add_error(
                "to_grade",
                "Defina um grau de destino ou cadastre a próxima faixa nesta faixa.",
            )
        return cleaned_data


class GraduationForm(forms.ModelForm):
    class Meta:
        model = Graduation
        fields = (
            "person",
            "belt_rank",
            "grade_number",
            "awarded_at",
            "awarded_by",
            "notes",
        )
        labels = {
            "person": "Pessoa",
            "belt_rank": "Faixa",
            "grade_number": "Grau",
            "awarded_at": "Concedida em",
            "awarded_by": "Concedida por",
            "notes": "Observações",
        }
        widgets = {
            "awarded_at": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person"].queryset = (
            Person.objects.filter(is_active=True).order_by("full_name")
        )
        self.fields["belt_rank"].queryset = BeltRank.objects.order_by("display_order", "display_name")
        self.fields["awarded_by"].queryset = (
            Person.objects.filter(
                Q(person_type__code=PersonTypeCode.INSTRUCTOR)
                | Q(person_type__code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT)
            )
            .order_by("full_name")
        )
        self.fields["awarded_by"].required = False
        self.fields["notes"].required = False

    def clean(self):
        cleaned_data = super().clean()
        belt_rank = cleaned_data.get("belt_rank")
        grade_number = cleaned_data.get("grade_number")
        if belt_rank and grade_number is not None and grade_number > belt_rank.max_grades:
            self.add_error("grade_number", "Grau acima do máximo permitido para a faixa.")
        return cleaned_data
