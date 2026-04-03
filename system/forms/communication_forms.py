from django import forms

from system.models import BulkCommunication, NoticeBoardMessage


class NoticeBoardMessageForm(forms.ModelForm):
    class Meta:
        model = NoticeBoardMessage
        fields = ("title", "body", "audience", "starts_at", "ends_at", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].widget = forms.DateTimeInput(attrs={"type": "datetime-local"})
        self.fields["ends_at"].widget = forms.DateTimeInput(attrs={"type": "datetime-local"})


class BulkCommunicationForm(forms.ModelForm):
    class Meta:
        model = BulkCommunication
        fields = ("title", "message", "audience", "channel")
