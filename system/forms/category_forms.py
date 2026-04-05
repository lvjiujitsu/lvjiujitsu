from django import forms

from system.models import ClassCategory


class ClassCategoryForm(forms.ModelForm):
    class Meta:
        model = ClassCategory
        fields = (
            "code",
            "display_name",
            "audience",
            "description",
            "display_order",
            "is_active",
        )
        labels = {
            "code": "Código técnico",
            "display_name": "Nome exibido",
            "audience": "Base da categoria",
            "description": "Descrição",
            "display_order": "Ordem de exibição",
            "is_active": "Categoria ativa",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
