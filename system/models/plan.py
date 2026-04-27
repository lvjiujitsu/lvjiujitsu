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


class PlanAudience(models.TextChoices):
    ADULT = "adult", "Adulto"
    KIDS_JUVENILE = "kids_juvenile", "Kids/Juvenil"


class PlanWeeklyFrequency(models.IntegerChoices):
    TWICE = 2, "2x por semana"
    FIVE_TIMES = 5, "5x por semana"


STRIPE_INTERVAL_BY_CYCLE = {
    BillingCycle.MONTHLY: ("month", 1),
    BillingCycle.QUARTERLY: ("month", 3),
    BillingCycle.SEMIANNUAL: ("month", 6),
    BillingCycle.ANNUAL: ("year", 1),
}

CYCLE_MONTHS = {
    BillingCycle.MONTHLY: 1,
    BillingCycle.QUARTERLY: 3,
    BillingCycle.SEMIANNUAL: 6,
    BillingCycle.ANNUAL: 12,
}


class SubscriptionPlan(TimeStampedModel):
    code = models.CharField("Código", max_length=80, unique=True)
    display_name = models.CharField("Nome", max_length=200)
    audience = models.CharField(
        "Público",
        max_length=20,
        choices=PlanAudience.choices,
        default=PlanAudience.ADULT,
    )
    weekly_frequency = models.PositiveSmallIntegerField(
        "Frequência semanal",
        choices=PlanWeeklyFrequency.choices,
        default=PlanWeeklyFrequency.FIVE_TIMES,
    )
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
    teacher_commission_percentage = models.DecimalField(
        "Repasse do professor (%)",
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    requires_special_authorization = models.BooleanField(
        "Exige autorização especial",
        default=False,
    )
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
