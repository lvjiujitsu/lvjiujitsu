from django import forms
from django.utils import timezone

from system.models import ExportRequest


class ReportCenterFilterForm(forms.Form):
    start_date = forms.DateField(label="Data inicial")
    end_date = forms.DateField(label="Data final")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        first_day = today.replace(day=1)
        self.fields["start_date"].initial = first_day
        self.fields["end_date"].initial = today

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "A data final nao pode ser anterior a inicial.")
        return cleaned_data


class ExportRequestForm(forms.Form):
    report_type = forms.ChoiceField(label="Tipo de relatorio", choices=ExportRequest.TYPE_CHOICES)
    start_date = forms.DateField(widget=forms.HiddenInput)
    end_date = forms.DateField(widget=forms.HiddenInput)
