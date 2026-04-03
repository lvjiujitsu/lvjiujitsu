from django import forms


class AttendanceCheckInForm(forms.Form):
    token = forms.CharField(label="Token QR", max_length=96)


class ManualAttendanceForm(forms.Form):
    student_uuid = forms.UUIDField(label="Aluno")
    reason = forms.CharField(label="Motivo", widget=forms.Textarea)
