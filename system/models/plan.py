from decimal import ROUND_HALF_UP, Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

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


def compute_gross_price(
    *,
    base_monthly_net_price,
    billing_cycle,
    cycle_discount_percentage=0,
    gateway_fixed_fee=0,
    gateway_percentage_fee=0,
):
    base = Decimal(str(base_monthly_net_price))
    n = Decimal(str(CYCLE_MONTHS.get(billing_cycle, 1)))
    disc = Decimal(str(cycle_discount_percentage or 0))
    fixed = Decimal(str(gateway_fixed_fee or 0))
    pct = Decimal(str(gateway_percentage_fee or 0))
    net_total = base * n * (1 - disc)
    if pct == 0:
        gross = net_total + fixed
    else:
        gross = (net_total + fixed) / (1 - pct)
    return gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
        default=0,
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
    is_loyalty_plan = models.BooleanField("Plano veterano", default=False)
    base_monthly_net_price = models.DecimalField(
        "Valor líquido mensal desejado",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Valor que a academia deseja receber por mês, antes das taxas do gateway.",
    )
    gateway_code = models.CharField(
        "Gateway",
        max_length=40,
        blank=True,
        default="",
        help_text="Ex: asaas_pix, asaas_card, stripe_card.",
    )
    gateway_fixed_fee = models.DecimalField(
        "Taxa fixa do gateway (R$)",
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    gateway_percentage_fee = models.DecimalField(
        "Taxa % do gateway",
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Decimal puro. Ex: 0.0429 = 4,29%.",
    )
    cycle_discount_percentage = models.DecimalField(
        "Desconto do ciclo",
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Decimal puro. Ex: 0.0257 = 2,57%.",
    )
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

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self.base_monthly_net_price is not None:
            self.price = self._compute_price()
            n_months = CYCLE_MONTHS.get(self.billing_cycle, 1)
            if n_months > 1:
                self.monthly_reference_price = (
                    self.price / Decimal(str(n_months))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                self.monthly_reference_price = None
            if update_fields is not None:
                update_fields = set(update_fields) | {"price", "monthly_reference_price"}
                kwargs["update_fields"] = update_fields
        super().save(*args, **kwargs)

    def _compute_price(self) -> Decimal:
        return compute_gross_price(
            base_monthly_net_price=self.base_monthly_net_price,
            billing_cycle=self.billing_cycle,
            cycle_discount_percentage=self.cycle_discount_percentage,
            gateway_fixed_fee=self.gateway_fixed_fee,
            gateway_percentage_fee=self.gateway_percentage_fee,
        )

    @property
    def stripe_interval(self):
        return STRIPE_INTERVAL_BY_CYCLE.get(self.billing_cycle)


class PlanTier(TimeStampedModel):
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
    family_discount_percentage = models.DecimalField(
        "Desconto família",
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=(
            "Decimal puro. Ex: 0.18 = 18%. Aplicado quando 2+ pessoas do "
            "grupo familiar compartilham este tier."
        ),
    )
    display_order = models.PositiveSmallIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ("display_order", "display_name")
        verbose_name = "Tier comercial"
        verbose_name_plural = "Tiers comerciais"
        indexes = [
            models.Index(fields=("audience", "weekly_frequency")),
        ]

    def __str__(self):
        return self.display_name


class PlanPrice(TimeStampedModel):
    tier = models.ForeignKey(
        PlanTier,
        on_delete=models.PROTECT,
        related_name="prices",
        verbose_name="Tier",
    )
    payment_method = models.CharField(
        "Meio de pagamento",
        max_length=16,
        choices=PlanPaymentMethod.choices,
        default=PlanPaymentMethod.CREDIT_CARD,
    )
    billing_cycle = models.CharField(
        "Ciclo de cobrança",
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )
    gateway_code = models.CharField(
        "Gateway",
        max_length=40,
        blank=True,
        default="",
        help_text="Ex: asaas_pix, asaas_card, stripe_card.",
    )
    base_monthly_net_price = models.DecimalField(
        "Valor líquido mensal desejado",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Valor que a academia deseja receber por mês, antes das taxas do gateway.",
    )
    cycle_discount_percentage = models.DecimalField(
        "Desconto do ciclo",
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Decimal puro. Ex: 0.0257 = 2,57%.",
    )
    gateway_fixed_fee = models.DecimalField(
        "Taxa fixa do gateway (R$)",
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    gateway_percentage_fee = models.DecimalField(
        "Taxa % do gateway",
        max_digits=6,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Decimal puro. Ex: 0.0429 = 4,29%.",
    )
    price = models.DecimalField(
        "Preço",
        max_digits=10,
        decimal_places=2,
        default=0,
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
    teacher_commission_percentage = models.DecimalField(
        "Repasse do professor (%)",
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    effective_from = models.DateTimeField("Vigente desde", default=timezone.now)
    effective_until = models.DateTimeField("Vigente até", null=True, blank=True)
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
        ordering = ("-effective_from",)
        verbose_name = "Preço de plano"
        verbose_name_plural = "Preços de plano"
        indexes = [
            models.Index(fields=("tier", "payment_method", "billing_cycle", "is_active")),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("tier", "gateway_code", "billing_cycle"),
                condition=models.Q(is_active=True),
                name="unique_active_plan_price_per_tier_gateway_cycle",
            ),
        ]

    def __str__(self):
        return f"{self.tier.display_name} — {self.get_payment_method_display()} ({self.get_billing_cycle_display()})"

    @property
    def display_name(self):
        return self.tier.display_name

    @property
    def audience(self):
        return self.tier.audience

    @property
    def weekly_frequency(self):
        return self.tier.weekly_frequency

    def save(self, *args, **kwargs):
        self._guard_immutability()
        self.price = compute_gross_price(
            base_monthly_net_price=self.base_monthly_net_price,
            billing_cycle=self.billing_cycle,
            cycle_discount_percentage=self.cycle_discount_percentage,
            gateway_fixed_fee=self.gateway_fixed_fee,
            gateway_percentage_fee=self.gateway_percentage_fee,
        )
        n_months = CYCLE_MONTHS.get(self.billing_cycle, 1)
        if n_months > 1:
            self.monthly_reference_price = (
                self.price / Decimal(str(n_months))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            self.monthly_reference_price = None
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            # 'price'/'monthly_reference_price' são derivados dos outros campos
            # dentro deste save(), não passados por quem chama — precisam entrar
            # explicitamente em update_fields, senão update_or_create() (usado
            # pelos seeds de catálogo) grava os campos base corretos mas deixa
            # o preço antigo intocado no banco.
            update_fields = set(update_fields) | {"price", "monthly_reference_price"}
            kwargs["update_fields"] = update_fields
        super().save(*args, **kwargs)

    def _guard_immutability(self):
        if not self.pk:
            return
        previous = PlanPrice.objects.filter(pk=self.pk).first()
        if previous is None or not previous.is_referenced_by_membership:
            return
        pricing_fields = (
            "tier_id",
            "payment_method",
            "billing_cycle",
            "base_monthly_net_price",
            "cycle_discount_percentage",
            "gateway_fixed_fee",
            "gateway_percentage_fee",
        )
        changed = any(
            getattr(previous, field) != getattr(self, field) for field in pricing_fields
        )
        if changed:
            raise ValueError(
                "PlanPrice já referenciada por um Membership é imutável; "
                "crie uma nova linha em vez de editar os campos de preço desta."
            )

    @property
    def is_referenced_by_membership(self):
        from system.models.membership import Membership

        return Membership.objects.filter(plan_price=self).exists()

    @property
    def stripe_interval(self):
        return STRIPE_INTERVAL_BY_CYCLE.get(self.billing_cycle)

    def family_price(self):
        discount = Decimal(str(self.tier.family_discount_percentage or 0))
        return (self.price * (1 - discount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def archive(self, *, until=None):
        self.is_active = False
        self.effective_until = until or timezone.now()
        self.save(update_fields=["is_active", "effective_until", "updated_at"])
