from django.db import models
from django.utils import timezone

from system.runtime_config import payment_currency

from .common import TimeStampedModel


class MembershipStatus(models.TextChoices):
    PENDING = "pending", "Aguardando pagamento"
    ACTIVE = "active", "Ativa"
    PAST_DUE = "past_due", "Em atraso"
    CANCELED = "canceled", "Cancelada"
    EXPIRED = "expired", "Expirada"
    EXEMPTED = "exempted", "Isenta"


class MembershipCreatedVia(models.TextChoices):
    CHECKOUT = "checkout", "Stripe Checkout"
    EXEMPTION = "exemption", "Isenção administrativa"
    MANUAL_PAID = "manual_paid", "Marcada como paga manualmente"
    MIGRATION = "migration", "Migração de dados"


class Membership(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Pessoa",
    )
    plan = models.ForeignKey(
        "system.SubscriptionPlan",
        on_delete=models.PROTECT,
        related_name="memberships",
        verbose_name="Plano",
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=MembershipStatus.choices,
        default=MembershipStatus.PENDING,
    )
    created_via = models.CharField(
        "Origem",
        max_length=16,
        choices=MembershipCreatedVia.choices,
        default=MembershipCreatedVia.CHECKOUT,
    )
    stripe_subscription_id = models.CharField(
        "Stripe Subscription ID",
        max_length=255,
        blank=True,
        default="",
    )
    stripe_customer_id = models.CharField(
        "Stripe Customer ID",
        max_length=120,
        blank=True,
        default="",
    )
    current_period_start = models.DateTimeField(
        "Início do ciclo atual",
        null=True,
        blank=True,
    )
    current_period_end = models.DateTimeField(
        "Fim do ciclo atual",
        null=True,
        blank=True,
    )
    cancel_at_period_end = models.BooleanField(
        "Cancelar no fim do período",
        default=False,
    )
    canceled_at = models.DateTimeField(
        "Cancelada em",
        null=True,
        blank=True,
    )
    activated_at = models.DateTimeField(
        "Ativada em",
        null=True,
        blank=True,
    )
    last_invoice_id = models.CharField(
        "Última invoice Stripe",
        max_length=255,
        blank=True,
        default="",
    )
    notes = models.TextField("Observações", blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        indexes = [
            models.Index(fields=("person", "status")),
            models.Index(fields=("stripe_subscription_id",)),
        ]

    def __str__(self):
        return f"Membership #{self.pk} — {self.person.full_name} ({self.get_status_display()})"

    @property
    def is_active_now(self):
        if self.status == MembershipStatus.EXEMPTED:
            return True
        if self.status == MembershipStatus.ACTIVE:
            if self.current_period_end is None:
                return True
            return self.current_period_end >= timezone.now()
        return False

    @property
    def grants_portal_access(self):
        return self.status in (
            MembershipStatus.ACTIVE,
            MembershipStatus.EXEMPTED,
            MembershipStatus.PAST_DUE,
        )


class MembershipInvoice(TimeStampedModel):
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name="Assinatura",
    )
    stripe_invoice_id = models.CharField(
        "Stripe Invoice ID",
        max_length=255,
        unique=True,
    )
    stripe_payment_intent_id = models.CharField(
        "PaymentIntent ID",
        max_length=255,
        blank=True,
        default="",
    )
    amount_paid = models.DecimalField(
        "Valor pago",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    amount_refunded = models.DecimalField(
        "Valor estornado",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    currency = models.CharField("Moeda", max_length=8, default=payment_currency)
    status = models.CharField("Status", max_length=32, default="paid")
    period_start = models.DateTimeField(
        "Início do período",
        null=True,
        blank=True,
    )
    period_end = models.DateTimeField(
        "Fim do período",
        null=True,
        blank=True,
    )
    hosted_invoice_url = models.URLField(
        "URL da fatura Stripe",
        blank=True,
        default="",
    )
    receipt_url = models.URLField(
        "URL do recibo",
        blank=True,
        default="",
    )
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    refunded_at = models.DateTimeField("Estornado em", null=True, blank=True)
    description = models.CharField(
        "Descrição",
        max_length=255,
        blank=True,
        default="",
    )

    class Meta:
        ordering = ("-paid_at", "-created_at")
        verbose_name = "Fatura da assinatura"
        verbose_name_plural = "Faturas das assinaturas"

    def __str__(self):
        return f"Invoice {self.stripe_invoice_id}"
