from decimal import ROUND_HALF_UP, Decimal

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
        null=True,
        blank=True,
    )
    plan_price = models.ForeignKey(
        "system.PlanPrice",
        on_delete=models.PROTECT,
        related_name="memberships",
        verbose_name="Preço do plano",
        null=True,
        blank=True,
    )
    family_discount_applied = models.BooleanField(
        "Desconto família aplicado",
        default=False,
    )
    billed_price = models.DecimalField(
        "Valor cobrado atualmente",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
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
    stripe_subscription_item_id = models.CharField(
        "Stripe Subscription Item ID",
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
    fidelity_extension_days = models.PositiveIntegerField(
        "Dias de prorrogação de carência",
        default=0,
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
    def effective_tier(self):
        if self.plan_price_id is not None:
            return self.plan_price.tier
        if self.plan_id is not None and not self.plan.is_loyalty_plan:
            from system.models.plan import PlanTier

            return PlanTier.objects.filter(
                audience=self.plan.audience,
                weekly_frequency=self.plan.weekly_frequency,
                is_active=True,
            ).first()
        return None

    @property
    def effective_full_price(self):
        if self.plan_price_id is not None:
            return self.plan_price.price
        if self.plan_id is not None:
            return self.plan.price
        return None

    @property
    def effective_display_name(self):
        if self.plan_price_id is not None:
            return self.plan_price.display_name
        if self.plan_id is not None:
            return self.plan.display_name
        return ""

    @property
    def effective_billing_cycle_display(self):
        if self.plan_price_id is not None:
            return self.plan_price.get_billing_cycle_display()
        if self.plan_id is not None:
            return self.plan.get_billing_cycle_display()
        return ""

    @property
    def effective_payment_method(self):
        if self.plan_price_id is not None:
            return self.plan_price.payment_method
        if self.plan_id is not None:
            return self.plan.payment_method
        return ""

    @property
    def effective_gateway_code(self):
        if self.plan_price_id is not None:
            return self.plan_price.gateway_code
        if self.plan_id is not None:
            return getattr(self.plan, "gateway_code", "")
        return ""

    @property
    def effective_payment_summary_label(self):
        method_labels = {"pix": "PIX", "credit_card": "Cartão de crédito"}
        gateway_labels = {
            "stripe_card": "Stripe (recorrente)",
            "asaas_pix": "Asaas",
            "asaas_card": "Asaas",
        }
        method = method_labels.get(self.effective_payment_method, "")
        gateway = gateway_labels.get(self.effective_gateway_code, "")
        if method and gateway:
            return f"{method} · {gateway}"
        return method or gateway

    def recompute_billed_price(self):
        full_price = self.effective_full_price
        if full_price is None:
            return
        tier = self.effective_tier
        if self.family_discount_applied and tier is not None:
            discount = Decimal(str(tier.family_discount_percentage or 0))
            self.billed_price = (full_price * (1 - discount)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            self.billed_price = full_price

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

    @property
    def is_stripe_recurring(self):
        return bool(self.stripe_subscription_id or self.effective_gateway_code == "stripe_card")

    @property
    def current_pause(self):
        today = timezone.localdate()
        return (
            self.pause_requests.filter(
                status=MembershipPauseRequestStatus.APPROVED,
                requested_start_date__lte=today,
                requested_end_date__gte=today,
            )
            .order_by("-requested_end_date")
            .first()
        )

    @property
    def is_currently_paused(self):
        return self.current_pause is not None


class MembershipCreditSource(models.TextChoices):
    PLAN_CHANGE_LEFTOVER = "plan_change_leftover", "Sobra de troca de plano"


class MembershipCreditStatus(models.TextChoices):
    AVAILABLE = "available", "Disponível"
    APPLIED = "applied", "Aplicado em renovação"
    REFUNDED = "refunded", "Devolvido ao cliente"


class MembershipCredit(TimeStampedModel):
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="credits",
        verbose_name="Assinatura",
    )
    amount = models.DecimalField(
        "Valor",
        max_digits=10,
        decimal_places=2,
    )
    source = models.CharField(
        "Origem",
        max_length=32,
        choices=MembershipCreditSource.choices,
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=MembershipCreditStatus.choices,
        default=MembershipCreditStatus.AVAILABLE,
    )
    source_order = models.ForeignKey(
        "system.RegistrationOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credits_generated",
        verbose_name="Pedido de origem",
    )
    applied_at = models.DateTimeField("Aplicado em", null=True, blank=True)
    refunded_at = models.DateTimeField("Devolvido em", null=True, blank=True)
    refund_provider = models.CharField(
        "Gateway do refund",
        max_length=16,
        blank=True,
        default="",
    )
    refund_provider_reference = models.CharField(
        "Referência do refund",
        max_length=255,
        blank=True,
        default="",
    )
    notes = models.TextField("Observações", blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Crédito da assinatura"
        verbose_name_plural = "Créditos das assinaturas"
        indexes = [
            models.Index(fields=("membership", "status")),
        ]

    def __str__(self):
        return (
            f"Crédito #{self.pk} — {self.membership.person.full_name} "
            f"R$ {self.amount} ({self.get_status_display()})"
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


class MembershipPauseRequestKind(models.TextChoices):
    MEDICAL = "medical", "Atestado médico"
    SELF_SERVICE = "self_service", "Trancamento"


class MembershipPauseRequestStatus(models.TextChoices):
    PENDING = "pending", "Aguardando aprovação"
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Recusada"
    CANCELED = "canceled", "Cancelada"


class MembershipPauseRequest(TimeStampedModel):
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="pause_requests",
        verbose_name="Assinatura",
    )
    kind = models.CharField(
        "Tipo",
        max_length=16,
        choices=MembershipPauseRequestKind.choices,
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=MembershipPauseRequestStatus.choices,
        default=MembershipPauseRequestStatus.PENDING,
    )
    requested_start_date = models.DateField("Início do período")
    requested_end_date = models.DateField("Fim do período")
    reason_note = models.TextField("Observação", blank=True, default="")
    decided_by = models.ForeignKey(
        "system.Person",
        on_delete=models.SET_NULL,
        related_name="decided_membership_pause_requests",
        verbose_name="Decidido por",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField("Decidido em", null=True, blank=True)
    decision_notes = models.TextField("Observações da decisão", blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Pausa de mensalidade"
        verbose_name_plural = "Pausas de mensalidade"

    def __str__(self):
        return (
            f"{self.membership.person.full_name} — "
            f"{self.get_kind_display()} ({self.get_status_display()})"
        )

    @property
    def duration_days(self):
        return (self.requested_end_date - self.requested_start_date).days + 1
