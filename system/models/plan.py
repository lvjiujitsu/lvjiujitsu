from django.core.validators import MinValueValidator
from django.db import models

from .common import TimeStampedModel


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly", "Mensal"
    QUARTERLY = "quarterly", "Trimestral"
    SEMIANNUAL = "semiannual", "Semestral"
    ANNUAL = "annual", "Anual"


class PlanPaymentMethod(models.TextChoices):
    PIX = "pix", "PIX"
    CREDIT_CARD = "credit_card", "Cartão de crédito"


STRIPE_INTERVAL_BY_CYCLE = {
    BillingCycle.MONTHLY: ("month", 1),
    BillingCycle.QUARTERLY: ("month", 3),
    BillingCycle.SEMIANNUAL: ("month", 6),
    BillingCycle.ANNUAL: ("year", 1),
}


class SubscriptionPlan(TimeStampedModel):
    code = models.CharField("Código", max_length=60, unique=True)
    display_name = models.CharField("Nome", max_length=200)
    billing_cycle = models.CharField(
        "Ciclo de cobrança",
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )
    price = models.DecimalField(
        "Preço",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    monthly_reference_price = models.DecimalField(
        "Preço mensal de referência",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    payment_method = models.CharField(
        "Meio de pagamento",
        max_length=16,
        choices=PlanPaymentMethod.choices,
        default=PlanPaymentMethod.CREDIT_CARD,
    )
    is_family_plan = models.BooleanField("Plano familiar", default=False)
    description = models.TextField("Descrição", blank=True, default="")
    display_order = models.PositiveSmallIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativo", default=True)
    stripe_product_id = models.CharField(
        "Stripe Product ID",
        max_length=120,
        blank=True,
        default="",
    )
    stripe_price_id = models.CharField(
        "Stripe Price ID (ativo)",
        max_length=120,
        blank=True,
        default="",
    )
    stripe_archived_price_ids = models.JSONField(
        "Stripe Price IDs arquivados",
        default=list,
        blank=True,
    )
    stripe_sync_error = models.TextField(
        "Erro da última sincronização com Stripe",
        blank=True,
        default="",
    )
    stripe_synced_at = models.DateTimeField(
        "Última sincronização com Stripe",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("display_order", "price")
        verbose_name = "Plano de assinatura"
        verbose_name_plural = "Planos de assinatura"

    def __str__(self):
        return self.display_name

    @property
    def stripe_interval(self):
        return STRIPE_INTERVAL_BY_CYCLE.get(self.billing_cycle)
