from django import forms

from system.core.dates import PT_BR_DATE_INPUT_FORMATS
from system.business_rule.models.membership import MembershipPauseRequestKind


class MembershipPauseRequestForm(forms.Form):
    kind = forms.ChoiceField(choices=MembershipPauseRequestKind.choices)
    start_date = forms.DateField(input_formats=PT_BR_DATE_INPUT_FORMATS)
    end_date = forms.DateField(input_formats=PT_BR_DATE_INPUT_FORMATS)
    reason_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class MembershipPauseDecisionForm(forms.Form):
    decision_notes = forms.CharField(
        required=False,
        label="Observação da decisão",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
