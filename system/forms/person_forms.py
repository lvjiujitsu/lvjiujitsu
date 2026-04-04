from django import forms

from system.models import Person, PersonType


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
    person_types = forms.ModelMultipleChoiceField(
        queryset=PersonType.objects.all(),
        required=False,
        label="Tipos de vínculo",
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
            "is_active",
            "user",
            "person_types",
        )
        labels = {
            "full_name": "Nome completo",
            "cpf": "CPF",
            "email": "E-mail",
            "phone": "Telefone",
            "birth_date": "Data de nascimento",
            "is_active": "Cadastro ativo",
            "user": "Usuário autenticável",
        }
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].required = False
        self.fields["person_types"].queryset = PersonType.objects.order_by("display_name")
        if self.instance.pk:
            self.fields["person_types"].initial = self.instance.person_types.all()

    def save(self, commit=True):
        person = super().save(commit=commit)
        person_types = self.cleaned_data.get("person_types")

        if commit:
            person.person_types.set(person_types)
        else:
            self._pending_person_types = person_types

        return person

    def save_m2m(self):
        super().save_m2m()
        if hasattr(self, "_pending_person_types"):
            self.instance.person_types.set(self._pending_person_types)
