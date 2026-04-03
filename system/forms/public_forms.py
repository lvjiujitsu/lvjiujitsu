from django import forms
from django.utils import timezone

from system.models import Lead, PublicPlan, TrialClassRequest


class LeadCaptureForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("full_name", "email", "phone", "source", "requested_plan", "interest_note")
        labels = {
            "full_name": "Nome completo",
            "email": "E-mail",
            "phone": "WhatsApp",
            "source": "Como voce conheceu a academia?",
            "requested_plan": "Plano de interesse",
            "interest_note": "Objetivo ou observacao",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["requested_plan"].queryset = PublicPlan.objects.filter(is_active=True)
        self.fields["requested_plan"].required = False


class TrialClassRequestPublicForm(forms.Form):
    full_name = forms.CharField(label="Nome completo", max_length=160)
    email = forms.EmailField(label="E-mail", required=False)
    phone = forms.CharField(label="WhatsApp", max_length=32, required=False)
    source = forms.ChoiceField(label="Como voce conheceu a academia?", choices=Lead.SOURCE_CHOICES)
    preferred_date = forms.DateField(label="Data desejada", widget=forms.DateInput(attrs={"type": "date"}))
    preferred_period = forms.ChoiceField(label="Periodo desejado", choices=TrialClassRequest.PERIOD_CHOICES)
    notes = forms.CharField(label="Observacoes", required=False, widget=forms.Textarea(attrs={"rows": 4}))

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("email") and not cleaned_data.get("phone"):
            raise forms.ValidationError("Informe ao menos e-mail ou WhatsApp.")
        preferred_date = cleaned_data.get("preferred_date")
        if preferred_date and preferred_date < timezone.localdate():
            self.add_error("preferred_date", "A aula experimental precisa ser solicitada para hoje ou futuro.")
        return cleaned_data
