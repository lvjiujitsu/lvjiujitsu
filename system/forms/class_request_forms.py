from django import forms
from django.db.models import Q

from system.models import (
    ClassCatalogRequestType,
    ClassCategory,
    ClassGroup,
    PixKeyType,
    TrainingStyle,
    WeekdayCode,
)
from system.utils import ensure_formatted_cpf


PAYOUT_METHOD_NONE = "none"
PAYOUT_METHOD_PIX = "pix"
PAYOUT_METHOD_BANK_ACCOUNT = "bank_account"


class ExistingTeacherClassCatalogRequestForm(forms.Form):
    request_type = forms.ChoiceField(
        choices=(
            (ClassCatalogRequestType.NEW_SCHEDULE, "Novo horário em turma existente"),
            (ClassCatalogRequestType.NEW_CLASS_GROUP, "Nova turma"),
        ),
        label="Tipo de solicitação",
    )
    class_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.none(),
        required=False,
        label="Turma existente",
        empty_label="Selecione",
    )
    class_category = forms.ModelChoiceField(
        queryset=ClassCategory.objects.none(),
        required=False,
        label="Categoria da nova turma",
        empty_label="Selecione",
    )
    display_name = forms.CharField(required=False, max_length=120, label="Nome da turma")
    weekday = forms.ChoiceField(choices=WeekdayCode.choices, label="Dia da semana")
    training_style = forms.ChoiceField(choices=TrainingStyle.choices, label="Estilo")
    start_time = forms.TimeField(
        label="Horário de início",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    duration_minutes = forms.IntegerField(
        min_value=15,
        max_value=360,
        initial=60,
        label="Duração em minutos",
    )
    default_capacity = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        label="Capacidade",
    )
    justification = forms.CharField(
        label="Justificativa",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, **kwargs):
        requester = kwargs.pop("requester")
        super().__init__(*args, **kwargs)
        self.fields["class_group"].queryset = _get_requester_class_groups(requester)
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get("request_type")
        if request_type == ClassCatalogRequestType.NEW_SCHEDULE:
            if cleaned_data.get("class_group") is None:
                self.add_error("class_group", "Selecione a turma existente.")
        if request_type == ClassCatalogRequestType.NEW_CLASS_GROUP:
            if cleaned_data.get("class_category") is None:
                self.add_error("class_category", "Selecione a categoria.")
            if not (cleaned_data.get("display_name") or "").strip():
                self.add_error("display_name", "Informe o nome da nova turma.")
        return cleaned_data


class NewTeacherClassCatalogRequestForm(forms.Form):
    full_name = forms.CharField(max_length=255, label="Nome completo")
    cpf = forms.CharField(max_length=14, label="CPF")
    email = forms.EmailField(required=False, label="E-mail")
    phone = forms.CharField(required=False, max_length=20, label="Telefone")
    password = forms.CharField(
        min_length=8,
        strip=False,
        label="Senha inicial",
        widget=forms.PasswordInput(),
    )
    password_confirm = forms.CharField(
        min_length=8,
        strip=False,
        label="Confirmar senha",
        widget=forms.PasswordInput(),
    )
    martial_art = forms.CharField(required=False, max_length=24, label="Modalidade")
    martial_art_graduation = forms.CharField(
        required=False,
        max_length=120,
        label="Graduação/nível",
    )
    jiu_jitsu_belt = forms.CharField(required=False, max_length=24, label="Faixa")
    jiu_jitsu_stripes = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=4,
        label="Graus",
    )
    class_category = forms.ModelChoiceField(
        queryset=ClassCategory.objects.none(),
        label="Categoria",
        empty_label="Selecione",
    )
    display_name = forms.CharField(max_length=120, label="Nome da turma")
    weekday = forms.ChoiceField(choices=WeekdayCode.choices, label="Dia da semana")
    training_style = forms.ChoiceField(choices=TrainingStyle.choices, label="Estilo")
    start_time = forms.TimeField(
        label="Horário de início",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    duration_minutes = forms.IntegerField(
        min_value=15,
        max_value=360,
        initial=60,
        label="Duração em minutos",
    )
    default_capacity = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        label="Capacidade",
    )
    payout_method = forms.ChoiceField(
        choices=(
            (PAYOUT_METHOD_NONE, "Informar depois"),
            (PAYOUT_METHOD_PIX, "PIX"),
            (PAYOUT_METHOD_BANK_ACCOUNT, "Conta bancária"),
        ),
        initial=PAYOUT_METHOD_NONE,
        label="Como quer receber?",
    )
    pix_key_type = forms.ChoiceField(
        choices=(("", "Selecione"),) + tuple(PixKeyType.choices),
        required=False,
        label="Tipo da chave PIX",
    )
    pix_key = forms.CharField(required=False, max_length=140, label="Chave PIX")
    bank_account_details = forms.CharField(
        required=False,
        label="Dados bancários",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    payout_holder_name = forms.CharField(
        required=False,
        max_length=140,
        label="Titular da conta",
    )
    payout_holder_document = forms.CharField(
        required=False,
        max_length=32,
        label="CPF/CNPJ do titular",
    )
    justification = forms.CharField(
        label="Justificativa",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")

    def clean_cpf(self):
        try:
            return ensure_formatted_cpf(self.cleaned_data.get("cpf", ""))
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password") or ""
        password_confirm = cleaned_data.get("password_confirm") or ""
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "As senhas não coincidem.")
        payout_method = cleaned_data.get("payout_method")
        if payout_method == PAYOUT_METHOD_PIX:
            if not cleaned_data.get("pix_key_type"):
                self.add_error("pix_key_type", "Selecione o tipo da chave PIX.")
            if not (cleaned_data.get("pix_key") or "").strip():
                self.add_error("pix_key", "Informe a chave PIX.")
        if payout_method == PAYOUT_METHOD_BANK_ACCOUNT and not (
            cleaned_data.get("bank_account_details") or ""
        ).strip():
            self.add_error("bank_account_details", "Informe os dados bancários.")
        return cleaned_data

    def get_payout_payload(self):
        return {
            "method": self.cleaned_data.get("payout_method") or PAYOUT_METHOD_NONE,
            "pix_key_type": self.cleaned_data.get("pix_key_type") or "",
            "pix_key": (self.cleaned_data.get("pix_key") or "").strip(),
            "bank_account_details": (
                self.cleaned_data.get("bank_account_details") or ""
            ).strip(),
            "holder_name": (self.cleaned_data.get("payout_holder_name") or "").strip(),
            "holder_document": (
                self.cleaned_data.get("payout_holder_document") or ""
            ).strip(),
        }


class ClassCatalogDecisionForm(forms.Form):
    class_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.none(),
        required=False,
        label="Turma existente",
        empty_label="Selecione",
    )
    class_category = forms.ModelChoiceField(
        queryset=ClassCategory.objects.none(),
        required=False,
        label="Categoria",
        empty_label="Selecione",
    )
    display_name = forms.CharField(required=False, max_length=120, label="Nome da turma")
    weekday = forms.ChoiceField(choices=WeekdayCode.choices, label="Dia da semana")
    training_style = forms.ChoiceField(choices=TrainingStyle.choices, label="Estilo")
    start_time = forms.TimeField(
        label="Horário de início",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    duration_minutes = forms.IntegerField(min_value=15, max_value=360, label="Duração")
    default_capacity = forms.IntegerField(required=False, min_value=0, label="Capacidade")
    decision_notes = forms.CharField(
        required=False,
        label="Observação da decisão",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        catalog_request = kwargs.pop("catalog_request")
        super().__init__(*args, **kwargs)
        self.catalog_request = catalog_request
        self.fields["class_group"].queryset = ClassGroup.objects.filter(
            is_active=True
        ).order_by("class_category__display_order", "class_category__display_name", "display_name")
        self.fields["class_category"].queryset = ClassCategory.objects.filter(
            is_active=True
        ).order_by("display_order", "display_name")
        join_existing = (
            catalog_request.request_type
            == ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS
        )
        if join_existing:
            for field_name in (
                "class_category",
                "display_name",
                "weekday",
                "training_style",
                "start_time",
                "duration_minutes",
                "default_capacity",
            ):
                self.fields[field_name].required = False
        self.initial.update(
            {
                "class_group": catalog_request.target_class_group_id,
                "class_category": catalog_request.class_category_id,
                "display_name": catalog_request.display_name,
                "weekday": catalog_request.weekday,
                "training_style": catalog_request.training_style,
                "start_time": catalog_request.start_time,
                "duration_minutes": catalog_request.duration_minutes,
                "default_capacity": catalog_request.default_capacity,
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        if (
            self.catalog_request.request_type
            == ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS
        ):
            if cleaned_data.get("class_group") is None:
                self.add_error("class_group", "Selecione a turma de vínculo.")
            return cleaned_data
        if self.catalog_request.request_type == ClassCatalogRequestType.NEW_SCHEDULE:
            if cleaned_data.get("class_group") is None:
                self.add_error("class_group", "Selecione a turma existente.")
        else:
            if cleaned_data.get("class_category") is None:
                self.add_error("class_category", "Selecione a categoria.")
            if not (cleaned_data.get("display_name") or "").strip():
                self.add_error("display_name", "Informe o nome da turma.")
        return cleaned_data


class ClassCatalogExtraScheduleForm(forms.Form):
    weekday = forms.ChoiceField(
        choices=(("", "—"),) + tuple(WeekdayCode.choices),
        required=False,
        label="Dia da semana",
    )
    training_style = forms.ChoiceField(
        choices=(("", "—"),) + tuple(TrainingStyle.choices),
        required=False,
        label="Estilo",
    )
    start_time = forms.TimeField(
        required=False,
        label="Horário",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    duration_minutes = forms.IntegerField(
        required=False,
        min_value=15,
        max_value=360,
        label="Duração (min)",
    )

    def clean(self):
        cleaned_data = super().clean()
        values = (
            cleaned_data.get("weekday"),
            cleaned_data.get("training_style"),
            cleaned_data.get("start_time"),
            cleaned_data.get("duration_minutes"),
        )
        if any(values) and not all(values):
            raise forms.ValidationError(
                "Preencha dia, estilo, horário e duração do horário adicional, ou deixe a linha em branco."
            )
        return cleaned_data

    def is_filled(self):
        return bool(self.cleaned_data.get("weekday"))


ClassCatalogExtraScheduleFormSet = forms.formset_factory(
    ClassCatalogExtraScheduleForm,
    extra=4,
    max_num=4,
)


def extract_extra_schedules(formset):
    extra_schedules = []
    for form in formset.forms:
        if not form.is_filled():
            continue
        extra_schedules.append(
            {
                "weekday": form.cleaned_data["weekday"],
                "training_style": form.cleaned_data["training_style"],
                "start_time": form.cleaned_data["start_time"],
                "duration_minutes": form.cleaned_data["duration_minutes"],
            }
        )
    return extra_schedules


class PayrollActivationForm(forms.Form):
    payroll_payment_day = forms.IntegerField(
        min_value=1,
        max_value=28,
        label="Dia de pagamento",
        initial=5,
    )
    payroll_activation_notes = forms.CharField(
        required=False,
        label="Observação da ativação",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


def _get_requester_class_groups(requester):
    if requester is None:
        return ClassGroup.objects.none()
    return (
        ClassGroup.objects.filter(is_active=True)
        .filter(Q(main_teacher=requester) | Q(instructor_assignments__person=requester))
        .distinct()
        .order_by("class_category__display_order", "class_category__display_name", "display_name")
    )
