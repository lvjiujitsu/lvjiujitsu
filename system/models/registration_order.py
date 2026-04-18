from django.conf import settings
from django.db import models

from .common import TimeStampedModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PAID = "paid", "Pago"
    FAILED = "failed", "Falhou"
    CANCELED = "canceled", "Cancelado"
    EXEMPTED = "exempted", "Isento"
    REFUNDED = "refunded", "Estornado"


class PaymentProvider(models.TextChoices):
    NONE = "", "Não definido"
    ASAAS = "asaas", "Asaas"
    STRIPE = "stripe", "Stripe"
    MANUAL = "manual", "Manual"


class DepositStatus(models.TextChoices):
    PENDING = "pending", "A receber"
    AVAILABLE = "available", "Disponível"
    DEPOSITED = "deposited", "Depositado"
    NOT_APPLICABLE = "not_applicable", "Não aplicável"


class ApprovalType(models.TextChoices):
    EXEMPT = "exempt", "Isento"
    MANUAL_PAID = "manual_paid", "Pago manualmente"


class OrderKind(models.TextChoices):
    SUBSCRIPTION = "subscription", "Assinatura"
    ONE_TIME = "one_time", "Avulso"


class RegistrationOrder(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="registration_orders",
        verbose_name="Pessoa",
    )
    plan = models.ForeignKey(
        "system.SubscriptionPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_orders",
        verbose_name="Plano",
    )
    plan_price = models.DecimalField(
        "Preço do plano",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total = models.DecimalField(
        "Total",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    notes = models.TextField("Observações", blank=True, default="")
    kind = models.CharField(
        "Tipo do pedido",
        max_length=16,
        choices=OrderKind.choices,
        default=OrderKind.SUBSCRIPTION,
    )
    payment_status = models.CharField(
        "Status do pagamento",
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    stripe_session_id = models.CharField(
        "ID da sessão Stripe",
        max_length=255,
        blank=True,
        default="",
    )
    stripe_payment_intent_id = models.CharField(
        "ID do PaymentIntent Stripe",
        max_length=255,
        blank=True,
        default="",
    )
    stripe_subscription_id = models.CharField(
        "ID da Assinatura Stripe",
        max_length=255,
        blank=True,
        default="",
    )
    asaas_payment_id = models.CharField(
        "ID do pagamento Asaas",
        max_length=120,
        blank=True,
        default="",
    )
    asaas_pix_qrcode = models.TextField(
        "QR Code PIX Asaas (base64)",
        blank=True,
        default="",
    )
    asaas_pix_copy_paste = models.TextField(
        "Copia e cola PIX Asaas",
        blank=True,
        default="",
    )
    asaas_pix_expires_at = models.DateTimeField(
        "PIX expira em",
        null=True,
        blank=True,
    )
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    refunded_at = models.DateTimeField("Estornado em", null=True, blank=True)
    approval_type = models.CharField(
        "Tipo de aprovação",
        max_length=16,
        choices=ApprovalType.choices,
        blank=True,
        default="",
    )
    approved_at = models.DateTimeField("Aprovado em", null=True, blank=True)
    approval_notes = models.TextField("Notas da aprovação", blank=True, default="")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_registration_orders",
        verbose_name="Aprovado por",
    )
    payment_provider = models.CharField(
        "Gateway",
        max_length=16,
        choices=PaymentProvider.choices,
        blank=True,
        default=PaymentProvider.NONE,
    )
    financial_transaction_id = models.CharField(
        "ID da transação financeira",
        max_length=255,
        blank=True,
        default="",
    )
    administrative_fee = models.DecimalField(
        "Taxa administrativa",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    net_amount = models.DecimalField(
        "Valor líquido",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    deposit_status = models.CharField(
        "Status de crédito",
        max_length=20,
        choices=DepositStatus.choices,
        default=DepositStatus.PENDING,
    )
    expected_deposit_date = models.DateField(
        "Previsão de crédito",
        null=True,
        blank=True,
    )
    deposited_at = models.DateTimeField(
        "Depositado em",
        null=True,
        blank=True,
    )
    is_plan_change = models.BooleanField(
        "Troca de plano",
        default=False,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Pedido de matrícula"
        verbose_name_plural = "Pedidos de matrícula"

    def __str__(self):
        return f"Pedido #{self.pk} — {self.person.full_name}"

    @property
    def is_paid(self):
        return self.payment_status in (PaymentStatus.PAID, PaymentStatus.EXEMPTED)

    @property
    def is_free(self):
        return self.total is not None and self.total <= 0

    @property
    def is_pending_admin_review(self):
        return (
            self.payment_status == PaymentStatus.PENDING
            and self.is_free
        )


class RegistrationOrderItem(TimeStampedModel):
    order = models.ForeignKey(
        RegistrationOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido",
    )
    product = models.ForeignKey(
        "system.Product",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
        verbose_name="Produto",
    )
    product_name = models.CharField("Nome do produto", max_length=200)
    quantity = models.PositiveIntegerField("Quantidade", default=1)
    unit_price = models.DecimalField(
        "Preço unitário",
        max_digits=10,
        decimal_places=2,
    )
    subtotal = models.DecimalField(
        "Subtotal",
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        ordering = ("pk",)
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens do pedido"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class StripeWebhookEvent(TimeStampedModel):
    event_id = models.CharField(
        "ID do evento Stripe",
        max_length=255,
        unique=True,
    )
    event_type = models.CharField("Tipo do evento", max_length=128)
    order = models.ForeignKey(
        RegistrationOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stripe_events",
        verbose_name="Pedido",
    )
    membership = models.ForeignKey(
        "system.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stripe_events",
        verbose_name="Assinatura",
    )
    payload = models.JSONField("Payload", default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Evento de webhook Stripe"
        verbose_name_plural = "Eventos de webhook Stripe"

    def __str__(self):
        return f"{self.event_type} — {self.event_id}"
