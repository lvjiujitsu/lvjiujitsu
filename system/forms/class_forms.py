from django import forms

from system.models import ClassDiscipline, ClassGroup, ClassSession, IbjjfBelt


class InstructorProfileForm(forms.Form):
    full_name = forms.CharField(label="Nome completo", max_length=255)
    cpf = forms.CharField(label="CPF", max_length=14)
    email = forms.EmailField(label="E-mail", required=False)
    belt_rank = forms.ModelChoiceField(label="Faixa", queryset=IbjjfBelt.objects.filter(is_active=True), required=False)
    bio = forms.CharField(label="Bio", widget=forms.Textarea, required=False)
    specialties = forms.CharField(label="Especialidades", widget=forms.Textarea, required=False)
    is_active = forms.BooleanField(label="Ativo", required=False, initial=True)


class ClassDisciplineForm(forms.ModelForm):
    class Meta:
        model = ClassDiscipline
        fields = ("name", "slug", "description", "is_active")


class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = (
            "name",
            "modality",
            "instructor",
            "reference_belt",
            "weekday",
            "start_time",
            "end_time",
            "capacity",
            "reservation_required",
            "minimum_age",
            "is_active",
        )


class ClassSessionForm(forms.ModelForm):
    class Meta:
        model = ClassSession
        fields = ("class_group", "starts_at", "ends_at", "status")
