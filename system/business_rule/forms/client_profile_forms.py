from django import forms
from system.core.dates import PT_BR_DATE_INPUT_FORMATS
from system.business_rule.models import MartialArt, Person


class ClientProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Data de nascimento",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    martial_art_started_at = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Início no treino",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    martial_art_last_graduation_at = forms.DateField(
        required=False,
        input_formats=PT_BR_DATE_INPUT_FORMATS,
        label="Última graduação",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    jiu_jitsu_stripes = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=4,
        label="Graus",
    )

    class Meta:
        model = Person
        fields = (
            "full_name",
            "birth_date",
            "biological_sex",
            "email",
            "phone",
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
        )
        labels = {
            "full_name": "Nome completo",
            "biological_sex": "Sexo biológico",
            "email": "E-mail",
            "phone": "Telefone",
            "postal_code": "CEP",
            "address": "Logradouro",
            "address_number": "Número",
            "address_complement": "Complemento",
            "address_neighborhood": "Bairro",
            "city": "Cidade",
            "blood_type": "Tipo sanguíneo",
            "allergies": "Alergias",
            "previous_injuries": "Lesões",
            "emergency_contact": "Contato de emergência",
            "martial_art": "Arte marcial",
            "martial_art_graduation": "Graduação",
            "jiu_jitsu_belt": "Faixa de Jiu Jitsu",
            "previous_academy": "Academia anterior",
        }
        widgets = {
            "allergies": forms.Textarea(attrs={"rows": 3}),
            "previous_injuries": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-input form-textarea")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-input form-select")
            else:
                widget.attrs.setdefault("class", "form-input")

    def clean(self):
        cleaned_data = super().clean()
        martial_art = cleaned_data.get("martial_art") or ""
        if martial_art == MartialArt.JIU_JITSU:
            cleaned_data["martial_art_graduation"] = ""
        elif martial_art:
            cleaned_data["jiu_jitsu_belt"] = ""
            cleaned_data["jiu_jitsu_stripes"] = None
        else:
            cleaned_data["martial_art_graduation"] = ""
            cleaned_data["jiu_jitsu_belt"] = ""
            cleaned_data["jiu_jitsu_stripes"] = None
            cleaned_data["martial_art_started_at"] = None
            cleaned_data["martial_art_last_graduation_at"] = None
            cleaned_data["previous_academy"] = ""
        return cleaned_data
