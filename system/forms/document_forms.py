from django import forms

from system.models import DocumentRecord


class DocumentRecordUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentRecord
        fields = (
            "document_type",
            "title",
            "version_label",
            "file",
            "subscription",
            "is_visible_to_owner",
            "notes",
        )


class CertificateLookupForm(forms.Form):
    certificate_code = forms.CharField(label="Codigo do certificado", max_length=32)

    def clean_certificate_code(self):
        return self.cleaned_data["certificate_code"].strip().upper()


class LgpdRequestDecisionForm(forms.Form):
    DECISION_APPROVE = "approve"
    DECISION_REJECT = "reject"

    DECISION_CHOICES = (
        (DECISION_APPROVE, "Aprovar"),
        (DECISION_REJECT, "Recusar"),
    )

    decision = forms.ChoiceField(choices=DECISION_CHOICES)
    processing_notes = forms.CharField(widget=forms.Textarea, required=False)
