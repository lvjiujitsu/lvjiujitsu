from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from system.models.base import BaseModel


class FinancialPlan(BaseModel):
    CYCLE_MONTHLY = "MONTHLY"
    CYCLE_QUARTERLY = "QUARTERLY"
    CYCLE_SEMIANNUAL = "SEMIANNUAL"
    CYCLE_ANNUAL = "ANNUAL"

    CYCLE_CHOICES = (
        (CYCLE_MONTHLY, "Mensal"),
        (CYCLE_QUARTERLY, "Trimestral"),
        (CYCLE_SEMIANNUAL, "Semestral"),
        (CYCLE_ANNUAL, "Anual"),
    )

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    billing_cycle = models.CharField(max_length=16, choices=CYCLE_CHOICES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    allows_pause = models.BooleanField(default=True)
    blocks_checkin_on_overdue = models.BooleanField(default=True)
    active_from = models.DateField(default=timezone.localdate)
    active_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def clean(self):
        super().clean()
        if self.active_until and self.active_until < self.active_from:
            raise ValidationError({"active_until": "Fim de vigencia nao pode ser anterior ao inicio."})

    def __str__(self):
        return self.name


class FinancialBenefit(BaseModel):
    TYPE_DISCOUNT = "DISCOUNT"
    TYPE_SCHOLARSHIP = "SCHOLARSHIP"
    TYPE_OTHER = "OTHER"

    VALUE_PERCENTAGE = "PERCENTAGE"
    VALUE_FIXED = "FIXED"

    TYPE_CHOICES = (
        (TYPE_DISCOUNT, "Desconto"),
        (TYPE_SCHOLARSHIP, "Bolsa"),
        (TYPE_OTHER, "Outro"),
    )
    VALUE_CHOICES = (
        (VALUE_PERCENTAGE, "Percentual"),
        (VALUE_FIXED, "Valor fixo"),
    )

    name = models.CharField(max_length=128)
    benefit_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    value_type = models.CharField(max_length=16, choices=VALUE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def clean(self):
        super().clean()
        if self.value <= Decimal("0"):
            raise ValidationError({"value": "Beneficio deve ser maior que zero."})
        if self.value_type == self.VALUE_PERCENTAGE and self.value > Decimal("100"):
            raise ValidationError({"value": "Percentual nao pode exceder 100."})

    def calculate_discount(self, base_amount):
        if self.value_type == self.VALUE_FIXED:
            return min(self.value, base_amount)
        percentage = (self.value / Decimal("100")) * base_amount
        return percentage.quantize(Decimal("0.01"))

    def __str__(self):
        return self.name


class LocalSubscription(BaseModel):
    STATUS_DRAFT = "DRAFT"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_PENDING_FINANCIAL = "PENDING_FINANCIAL"
    STATUS_PAUSED = "PAUSED"
    STATUS_BLOCKED = "BLOCKED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Rascunho"),
        (STATUS_ACTIVE, "Ativa"),
        (STATUS_PENDING_FINANCIAL, "Pendente financeiro"),
        (STATUS_PAUSED, "Pausada"),
        (STATUS_BLOCKED, "Bloqueada"),
        (STATUS_CANCELLED, "Cancelada"),
    )

    plan = models.ForeignKey(
        FinancialPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    responsible_user = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.PROTECT,
        related_name="financial_subscriptions",
    )
    benefit = models.ForeignKey(
        FinancialBenefit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Encerramento nao pode ser anterior ao inicio."})

    def __str__(self):
        return f"{self.responsible_user.full_name} - {self.plan.name}"


class SubscriptionStudent(BaseModel):
    subscription = models.ForeignKey(
        LocalSubscription,
        on_delete=models.CASCADE,
        related_name="covered_students",
    )
    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="subscription_links",
    )
    student_benefit = models.ForeignKey(
        FinancialBenefit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_students",
    )
    is_primary_student = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("subscription", "student__user__full_name")
        constraints = [
            models.UniqueConstraint(
                fields=("subscription", "student"),
                name="uniq_subscription_student_link",
            )
        ]

    def __str__(self):
        return f"{self.subscription} -> {self.student.user.full_name}"


class MonthlyInvoice(BaseModel):
    STATUS_OPEN = "OPEN"
    STATUS_PAID = "PAID"
    STATUS_OVERDUE = "OVERDUE"
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = (
        (STATUS_OPEN, "Aberta"),
        (STATUS_PAID, "Paga"),
        (STATUS_OVERDUE, "Vencida"),
        (STATUS_UNDER_REVIEW, "Em analise"),
        (STATUS_CANCELLED, "Cancelada"),
    )

    subscription = models.ForeignKey(
        LocalSubscription,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    reference_month = models.DateField()
    due_date = models.DateField()
    amount_gross = models.DecimalField(max_digits=10, decimal_places=2)
    amount_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_net = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    paid_at = models.DateTimeField(null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-reference_month", "-due_date")
        constraints = [
            models.UniqueConstraint(
                fields=("subscription", "reference_month"),
                name="uniq_subscription_invoice_month",
            )
        ]

    def clean(self):
        super().clean()
        if self.amount_net != (self.amount_gross - self.amount_discount):
            raise ValidationError({"amount_net": "Valor liquido deve refletir bruto menos desconto."})

    def __str__(self):
        return f"{self.subscription} - {self.reference_month:%m/%Y}"


class EnrollmentPause(BaseModel):
    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="enrollment_pauses",
    )
    subscription = models.ForeignKey(
        LocalSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pauses",
    )
    reason = models.CharField(max_length=255)
    start_date = models.DateField(default=timezone.localdate)
    expected_return_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-start_date",)

    def clean(self):
        super().clean()
        if self.expected_return_date and self.expected_return_date < self.start_date:
            raise ValidationError({"expected_return_date": "Retorno previsto nao pode ser anterior ao inicio."})
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Fim da pausa nao pode ser anterior ao inicio."})

    def __str__(self):
        return f"{self.student.user.full_name} - pausa"


def payment_proof_upload_to(instance, filename):
    return f"payment_proofs/{timezone.now():%Y/%m/%d}/{filename}"


class PaymentProof(BaseModel):
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = (
        (STATUS_UNDER_REVIEW, "Em analise"),
        (STATUS_APPROVED, "Aprovado"),
        (STATUS_REJECTED, "Reprovado"),
    )

    invoice = models.ForeignKey(
        MonthlyInvoice,
        on_delete=models.CASCADE,
        related_name="payment_proofs",
    )
    uploaded_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.PROTECT,
        related_name="uploaded_payment_proofs",
    )
    reviewed_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payment_proofs",
    )
    file = models.FileField(upload_to=payment_proof_upload_to)
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_UNDER_REVIEW)
    submitted_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-submitted_at",)

    def clean(self):
        super().clean()
        if not self.file:
            return
        extension = Path(self.file.name).suffix.lower().lstrip(".")
        allowed_extensions = {item.strip().lower() for item in settings.MANUAL_PAYMENT_PROOF_ALLOWED_EXTENSIONS}
        if extension not in allowed_extensions:
            raise ValidationError({"file": "Extensao de comprovante nao permitida."})
        max_size = settings.MANUAL_PAYMENT_PROOF_MAX_SIZE_MB * 1024 * 1024
        if self.file.size > max_size:
            raise ValidationError({"file": "Arquivo excede o tamanho maximo permitido."})

    def __str__(self):
        return f"Comprovante {self.invoice}"


class PdvProduct(BaseModel):
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "name")

    def clean(self):
        super().clean()
        if self.unit_price <= Decimal("0.00"):
            raise ValidationError({"unit_price": "O valor unitario precisa ser maior que zero."})

    def __str__(self):
        return f"{self.name} ({self.sku})"


class CashSession(BaseModel):
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"

    STATUS_CHOICES = (
        (STATUS_OPEN, "Aberto"),
        (STATUS_CLOSED, "Fechado"),
    )

    operator_user = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.PROTECT,
        related_name="cash_sessions",
    )
    opened_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.PROTECT,
        related_name="opened_cash_sessions",
    )
    closed_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_cash_sessions",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    expected_cash_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    counted_cash_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    difference_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    requires_manager_review = models.BooleanField(default=False)
    manager_alert_reason = models.CharField(max_length=255, blank=True)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-opened_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("operator_user",),
                condition=Q(status="OPEN"),
                name="uniq_open_cash_session_per_operator",
            )
        ]

    def clean(self):
        super().clean()
        if self.opening_balance < Decimal("0.00"):
            raise ValidationError({"opening_balance": "A abertura do caixa nao pode ser negativa."})
        if self.status == self.STATUS_OPEN and self.closed_at is not None:
            raise ValidationError({"closed_at": "Caixa aberto nao pode possuir encerramento."})
        if self.status == self.STATUS_CLOSED and self.closed_at is None:
            raise ValidationError({"closed_at": "Caixa fechado precisa registrar encerramento."})
        if self.counted_cash_total is not None and self.counted_cash_total < Decimal("0.00"):
            raise ValidationError({"counted_cash_total": "O valor contado nao pode ser negativo."})

    @property
    def is_open(self):
        return self.status == self.STATUS_OPEN

    @property
    def requires_attention(self):
        return self.requires_manager_review

    def __str__(self):
        return f"Caixa {self.operator_user.full_name} - {self.get_status_display()}"


class PdvSale(BaseModel):
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    PAYMENT_CASH = "CASH"
    PAYMENT_PIX = "PIX"
    PAYMENT_CARD = "CARD"
    PAYMENT_TRANSFER = "TRANSFER"
    PAYMENT_OTHER = "OTHER"

    STATUS_CHOICES = (
        (STATUS_COMPLETED, "Concluida"),
        (STATUS_CANCELLED, "Cancelada"),
    )
    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_CASH, "Dinheiro"),
        (PAYMENT_PIX, "Pix"),
        (PAYMENT_CARD, "Cartao"),
        (PAYMENT_TRANSFER, "Transferencia"),
        (PAYMENT_OTHER, "Outro"),
    )

    cash_session = models.ForeignKey(
        CashSession,
        on_delete=models.PROTECT,
        related_name="sales",
    )
    operator_user = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.PROTECT,
        related_name="pdv_sales",
    )
    customer_student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pdv_sales",
    )
    customer_name_snapshot = models.CharField(max_length=255, blank=True)
    receipt_code = models.CharField(max_length=32, unique=True)
    payment_method = models.CharField(max_length=16, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    completed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-completed_at", "-created_at")

    def clean(self):
        super().clean()
        if self.total_amount != (self.subtotal_amount - self.discount_amount):
            raise ValidationError({"total_amount": "O total da venda precisa refletir subtotal menos desconto."})
        if self.total_amount <= Decimal("0.00"):
            raise ValidationError({"total_amount": "A venda precisa ter total positivo."})
        if self.payment_method == self.PAYMENT_CASH and self.amount_received < self.total_amount:
            raise ValidationError({"amount_received": "Pagamento em dinheiro precisa cobrir o total da venda."})
        if self.payment_method != self.PAYMENT_CASH and self.change_amount != Decimal("0.00"):
            raise ValidationError({"change_amount": "Apenas vendas em dinheiro podem gerar troco."})

    def __str__(self):
        return f"{self.receipt_code} - {self.total_amount}"


class PdvSaleItem(BaseModel):
    sale = models.ForeignKey(
        PdvSale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        PdvProduct,
        on_delete=models.PROTECT,
        related_name="sale_items",
    )
    product_name_snapshot = models.CharField(max_length=128)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ("created_at",)

    def clean(self):
        super().clean()
        expected_total = self.unit_price * self.quantity
        if self.quantity < 1:
            raise ValidationError({"quantity": "A quantidade precisa ser maior que zero."})
        if self.line_total != expected_total:
            raise ValidationError({"line_total": "O item precisa refletir valor unitario vezes quantidade."})

    def __str__(self):
        return f"{self.product_name_snapshot} x{self.quantity}"


class CashMovement(BaseModel):
    TYPE_OPENING = "OPENING"
    TYPE_SALE_IN = "SALE_IN"
    TYPE_CHANGE_OUT = "CHANGE_OUT"

    DIRECTION_IN = "IN"
    DIRECTION_OUT = "OUT"

    TYPE_CHOICES = (
        (TYPE_OPENING, "Abertura"),
        (TYPE_SALE_IN, "Entrada de venda"),
        (TYPE_CHANGE_OUT, "Troco"),
    )
    DIRECTION_CHOICES = (
        (DIRECTION_IN, "Entrada"),
        (DIRECTION_OUT, "Saida"),
    )

    cash_session = models.ForeignKey(
        CashSession,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    sale = models.ForeignKey(
        PdvSale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cash_movements",
    )
    created_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cash_movements_created",
    )
    movement_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    direction = models.CharField(max_length=8, choices=DIRECTION_CHOICES)
    payment_method = models.CharField(max_length=16, choices=PdvSale.PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "A movimentacao precisa ter valor positivo."})

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.amount}"
