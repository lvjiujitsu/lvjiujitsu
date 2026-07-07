from django import forms

from system.models.membership import MembershipPauseRequestKind


class MembershipPauseRequestForm(forms.Form):
    kind = forms.ChoiceField(choices=MembershipPauseRequestKind.choices)
    start_date = forms.DateField(input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    end_date = forms.DateField(input_formats=["%d/%m/%Y", "%Y-%m-%d"])
    reason_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class MembershipPauseDecisionForm(forms.Form):
    decision_notes = forms.CharField(
        required=False,
        label="Observação da decisão",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
