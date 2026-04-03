from decimal import Decimal

from django import forms
from django.forms import formset_factory

from system.models import (
    CashSession,
    FinancialBenefit,
    FinancialPlan,
    LocalSubscription,
    MonthlyInvoice,
    PdvProduct,
    PdvSale,
    StudentProfile,
)
from system.selectors.finance_selectors import get_active_financial_plans
from system.services.auth.cpf import normalize_cpf


class FinancialPlanForm(forms.ModelForm):
    class Meta:
        model = FinancialPlan
        fields = (
            "name",
            "slug",
            "billing_cycle",
            "base_price",
            "description",
            "allows_pause",
            "blocks_checkin_on_overdue",
            "active_from",
            "active_until",
            "is_active",
        )


class FinancialBenefitForm(forms.ModelForm):
    class Meta:
        model = FinancialBenefit
        fields = (
            "name",
            "benefit_type",
            "value_type",
            "value",
            "description",
            "is_active",
        )


class PdvProductForm(forms.ModelForm):
    class Meta:
        model = PdvProduct
        fields = ("sku", "name", "description", "unit_price", "display_order", "is_active")


class LocalSubscriptionCreateForm(forms.Form):
    plan = forms.ModelChoiceField(label="Plano", queryset=FinancialPlan.objects.none())
    responsible_full_name = forms.CharField(label="Nome do responsavel", max_length=255)
    responsible_cpf = forms.CharField(label="CPF do responsavel", max_length=14)
    responsible_email = forms.EmailField(label="E-mail do responsavel", required=False)
    benefit = forms.ModelChoiceField(
        label="Beneficio do contrato",
        queryset=FinancialBenefit.objects.none(),
        required=False,
    )
    students = forms.ModelMultipleChoiceField(
        label="Alunos cobertos",
        queryset=StudentProfile.objects.none(),
    )
    primary_student = forms.ModelChoiceField(
        label="Aluno principal",
        queryset=StudentProfile.objects.none(),
        required=False,
    )
    status = forms.ChoiceField(label="Status inicial", choices=LocalSubscription.STATUS_CHOICES)
    notes = forms.CharField(label="Observacoes", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_querysets()
        self.fields["status"].initial = LocalSubscription.STATUS_ACTIVE

    def clean(self):
        cleaned_data = super().clean()
        self._validate_students(cleaned_data)
        return cleaned_data

    def clean_responsible_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["responsible_cpf"])
        if not cpf:
            raise forms.ValidationError("Informe um CPF valido.")
        return cpf

    def _configure_querysets(self):
        active_students = StudentProfile.objects.select_related("user").filter(is_active=True).order_by("user__full_name")
        active_benefits = FinancialBenefit.objects.filter(is_active=True).order_by("name")
        self.fields["plan"].queryset = get_active_financial_plans()
        self.fields["benefit"].queryset = active_benefits
        self.fields["students"].queryset = active_students
        self.fields["primary_student"].queryset = active_students

    def _validate_students(self, cleaned_data):
        students = list(cleaned_data.get("students") or [])
        primary_student = cleaned_data.get("primary_student")
        if not students:
            raise forms.ValidationError("Selecione ao menos um aluno para o contrato.")
        if primary_student and primary_student not in students:
            self.add_error("primary_student", "O aluno principal precisa estar entre os alunos cobertos.")


class MonthlyInvoiceCreateForm(forms.Form):
    subscription = forms.ModelChoiceField(label="Assinatura", queryset=LocalSubscription.objects.none())
    reference_month = forms.DateField(label="Mes de referencia")
    due_date = forms.DateField(label="Vencimento")
    amount_gross = forms.DecimalField(label="Valor bruto", max_digits=10, decimal_places=2, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = LocalSubscription.objects.select_related("plan", "responsible_user").exclude(
            status=LocalSubscription.STATUS_CANCELLED
        )
        self.fields["subscription"].queryset = queryset.order_by("-created_at")

    def clean_reference_month(self):
        reference_month = self.cleaned_data["reference_month"]
        return reference_month.replace(day=1)

    def clean_amount_gross(self):
        amount_gross = self.cleaned_data.get("amount_gross")
        if amount_gross in (None, ""):
            return None
        if amount_gross <= Decimal("0.00"):
            raise forms.ValidationError("Informe um valor bruto maior que zero.")
        return amount_gross

    def clean(self):
        cleaned_data = super().clean()
        reference_month = cleaned_data.get("reference_month")
        due_date = cleaned_data.get("due_date")
        if reference_month and due_date and due_date < reference_month:
            self.add_error("due_date", "O vencimento nao pode ser anterior ao mes de referencia.")
        return cleaned_data


class EnrollmentPauseCreateForm(forms.Form):
    student = forms.ModelChoiceField(label="Aluno", queryset=StudentProfile.objects.none())
    subscription = forms.ModelChoiceField(
        label="Assinatura relacionada",
        queryset=LocalSubscription.objects.none(),
        required=False,
    )
    reason = forms.CharField(label="Motivo", max_length=255)
    start_date = forms.DateField(label="Inicio")
    expected_return_date = forms.DateField(label="Retorno previsto", required=False)
    notes = forms.CharField(label="Observacoes", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_students = StudentProfile.objects.select_related("user").filter(is_active=True).order_by("user__full_name")
        active_subscriptions = LocalSubscription.objects.select_related("plan", "responsible_user").exclude(
            status=LocalSubscription.STATUS_CANCELLED
        )
        self.fields["student"].queryset = active_students
        self.fields["subscription"].queryset = active_subscriptions.order_by("-created_at")

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        subscription = cleaned_data.get("subscription")
        expected_return_date = cleaned_data.get("expected_return_date")
        start_date = cleaned_data.get("start_date")
        if expected_return_date and start_date and expected_return_date < start_date:
            self.add_error("expected_return_date", "O retorno previsto nao pode ser anterior ao inicio da pausa.")
        if subscription and student and not subscription.covered_students.filter(student=student, is_active=True).exists():
            self.add_error("subscription", "A assinatura selecionada nao cobre este aluno.")
        return cleaned_data


class PaymentProofUploadForm(forms.Form):
    invoice_uuid = forms.UUIDField(widget=forms.HiddenInput)
    uploaded_file = forms.FileField(label="Arquivo do comprovante")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.invoice = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        self._resolve_invoice(cleaned_data.get("invoice_uuid"))
        return cleaned_data

    def get_invoice(self):
        return self.invoice

    def _resolve_invoice(self, invoice_uuid):
        if not invoice_uuid:
            return
        queryset = MonthlyInvoice.objects.select_related("subscription").filter(subscription__responsible_user=self.user)
        self.invoice = queryset.filter(uuid=invoice_uuid).first()
        if self.invoice is None:
            raise forms.ValidationError("Voce nao pode enviar comprovante para esta fatura.")


class PaymentProofReviewForm(forms.Form):
    DECISION_APPROVE = "approve"
    DECISION_REJECT = "reject"

    DECISION_CHOICES = (
        (DECISION_APPROVE, "Aprovar"),
        (DECISION_REJECT, "Reprovar"),
    )

    decision = forms.ChoiceField(label="Decisao", choices=DECISION_CHOICES)
    review_notes = forms.CharField(label="Observacoes da revisao", widget=forms.Textarea, required=False)

    def should_approve(self):
        return self.cleaned_data["decision"] == self.DECISION_APPROVE


class CashSessionOpenForm(forms.Form):
    opening_balance = forms.DecimalField(label="Fundo de abertura", max_digits=10, decimal_places=2, initial=Decimal("0.00"))
    notes = forms.CharField(label="Observacoes", widget=forms.Textarea, required=False)

    def clean_opening_balance(self):
        amount = self.cleaned_data["opening_balance"]
        if amount < Decimal("0.00"):
            raise forms.ValidationError("O fundo de abertura nao pode ser negativo.")
        return amount


class CashSessionCloseForm(forms.Form):
    counted_cash_total = forms.DecimalField(label="Valor contado", max_digits=10, decimal_places=2)
    notes = forms.CharField(label="Observacoes do fechamento", widget=forms.Textarea, required=False)

    def clean_counted_cash_total(self):
        amount = self.cleaned_data["counted_cash_total"]
        if amount < Decimal("0.00"):
            raise forms.ValidationError("O valor contado nao pode ser negativo.")
        return amount


class PdvSaleForm(forms.Form):
    student_query = forms.CharField(label="Aluno identificado (CPF ou nome)", max_length=255, required=False)
    payment_method = forms.ChoiceField(label="Meio de pagamento", choices=PdvSale.PAYMENT_METHOD_CHOICES)
    amount_received = forms.DecimalField(
        label="Valor recebido",
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    notes = forms.CharField(label="Observacoes", widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        self.student = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        self.student = self._resolve_student(cleaned_data.get("student_query", ""))
        amount_received = cleaned_data.get("amount_received")
        payment_method = cleaned_data.get("payment_method")
        if payment_method == PdvSale.PAYMENT_CASH and amount_received is None:
            self.add_error("amount_received", "Informe o valor recebido para vendas em dinheiro.")
        return cleaned_data

    def get_student(self):
        return self.student

    def _resolve_student(self, value):
        query = value.strip()
        if not query:
            return None
        normalized_cpf = normalize_cpf(query)
        queryset = StudentProfile.objects.select_related("user").filter(is_active=True)
        if normalized_cpf:
            student = queryset.filter(user__cpf=normalized_cpf).first()
            if student is None:
                raise forms.ValidationError("Nao existe aluno ativo com o CPF informado.")
            return student
        matches = list(queryset.filter(user__full_name__icontains=query)[:2])
        if not matches:
            raise forms.ValidationError("Nao foi encontrado aluno com este nome.")
        if len(matches) > 1:
            raise forms.ValidationError("Refine a busca do aluno para evitar ambiguidade.")
        return matches[0]


class PdvSaleItemForm(forms.Form):
    product = forms.ModelChoiceField(label="Produto", queryset=PdvProduct.objects.none(), required=False)
    quantity = forms.IntegerField(label="Quantidade", min_value=1, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = PdvProduct.objects.filter(is_active=True).order_by("display_order", "name")
        self.fields["product"].queryset = queryset

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        quantity = cleaned_data.get("quantity")
        if not product and not quantity:
            cleaned_data["skip_form"] = True
            return cleaned_data
        if product is None or quantity is None:
            raise forms.ValidationError("Informe produto e quantidade para cada item.")
        return cleaned_data


class BasePdvSaleItemFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        has_item = False
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get("skip_form"):
                continue
            has_item = True
        if not has_item:
            raise forms.ValidationError("Adicione pelo menos um item a venda.")


PdvSaleItemFormSet = formset_factory(
    PdvSaleItemForm,
    formset=BasePdvSaleItemFormSet,
    extra=3,
)
