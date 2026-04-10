from django.core.validators import MinValueValidator
from django.db import models

from .common import TimeStampedModel


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly", "Mensal"
    QUARTERLY = "quarterly", "Trimestral"
    SEMIANNUAL = "semiannual", "Semestral"
    ANNUAL = "annual", "Anual"


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
    description = models.TextField("Descrição", blank=True, default="")
    display_order = models.PositiveSmallIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ("display_order", "price")
        verbose_name = "Plano de assinatura"
        verbose_name_plural = "Planos de assinatura"

    def __str__(self):
        return self.display_name
