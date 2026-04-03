from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from system.models.base import BaseModel


class StripeCustomerLink(BaseModel):
    user = models.OneToOneField(
        "system.SystemUser",
        on_delete=models.CASCADE,
        related_name="stripe_customer_link",
    )
    stripe_customer_id = models.CharField(max_length=64, unique=True)
    livemode = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("user__full_name",)

    def __str__(self):
        return f"{self.user.full_name} -> {self.stripe_customer_id}"


class StripePlanPriceMap(BaseModel):
    plan = models.ForeignKey(
        "system.FinancialPlan",
        on_delete=models.CASCADE,
        related_name="stripe_price_maps",
    )
    stripe_product_id = models.CharField(max_length=64)
    stripe_price_id = models.CharField(max_length=64, unique=True)
    product_name = models.CharField(max_length=255, blank=True)
    lookup_key = models.CharField(max_length=128, blank=True)
    currency = models.CharField(max_length=8, default="brl")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    recurring_interval = models.CharField(max_length=16, blank=True)
    recurring_interval_count = models.PositiveSmallIntegerField(default=1)
    livemode = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)
    is_legacy = models.BooleanField(default=False)
    supports_pause_collection = models.BooleanField(default=True)
    valid_from = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("plan__name", "-is_current", "-valid_from")
        constraints = [
            models.UniqueConstraint(
                fields=("plan",),
                condition=Q(is_current=True, is_active=True),
                name="uniq_active_current_price_map_per_plan",
            )
        ]

    def clean(self):
        super().clean()
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError({"valid_until": "Fim de vigencia nao pode ser anterior ao inicio."})
        if self.is_current and self.is_legacy:
            raise ValidationError({"is_legacy": "Price vigente nao pode ser marcado como legado ao mesmo tempo."})
        if self.is_current and self.is_active:
            conflicting = self.__class__.objects.filter(plan=self.plan, is_current=True, is_active=True).exclude(pk=self.pk)
            if conflicting.exists():
                raise ValidationError({"is_current": "Ja existe um Price vigente ativo para este plano."})

    def __str__(self):
        return f"{self.plan.name} -> {self.stripe_price_id}"


class StripeSubscriptionLink(BaseModel):
    STATUS_PENDING = "PENDING"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_PAST_DUE = "PAST_DUE"
    STATUS_PAUSED_COLLECTION = "PAUSED_COLLECTION"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_UNKNOWN = "UNKNOWN"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pendente"),
        (STATUS_ACTIVE, "Ativa"),
        (STATUS_PAST_DUE, "Past due"),
        (STATUS_PAUSED_COLLECTION, "Pausa de cobranca"),
        (STATUS_CANCELLED, "Cancelada"),
        (STATUS_UNKNOWN, "Desconhecida"),
    )

    local_subscription = models.OneToOneField(
        "system.LocalSubscription",
        on_delete=models.CASCADE,
        related_name="stripe_subscription_link",
    )
    customer_link = models.ForeignKey(
        StripeCustomerLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_links",
    )
    price_map = models.ForeignKey(
        StripePlanPriceMap,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_links",
    )
    stripe_subscription_id = models.CharField(max_length=64, unique=True)
    stripe_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    pause_collection_behavior = models.CharField(max_length=32, blank=True)
    pause_collection_resumes_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    livemode = models.BooleanField(default=False)
    latest_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.local_subscription} -> {self.stripe_subscription_id}"


class CheckoutRequest(BaseModel):
    STATUS_CREATED = "CREATED"
    STATUS_SESSION_CREATED = "SESSION_CREATED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_EXPIRED = "EXPIRED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = (
        (STATUS_CREATED, "Criada"),
        (STATUS_SESSION_CREATED, "Sessao criada"),
        (STATUS_COMPLETED, "Concluida"),
        (STATUS_EXPIRED, "Expirada"),
        (STATUS_FAILED, "Falhou"),
    )

    requester = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.PROTECT,
        related_name="checkout_requests",
    )
    local_subscription = models.ForeignKey(
        "system.LocalSubscription",
        on_delete=models.CASCADE,
        related_name="checkout_requests",
    )
    customer_link = models.ForeignKey(
        StripeCustomerLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkout_requests",
    )
    price_map = models.ForeignKey(
        StripePlanPriceMap,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkout_requests",
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CREATED)
    stripe_checkout_session_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=64, null=True, blank=True)
    success_url = models.URLField()
    cancel_url = models.URLField()
    checkout_url = models.URLField(blank=True)
    metadata_snapshot = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.local_subscription} - {self.get_status_display()}"


class WebhookProcessing(BaseModel):
    STATUS_RECEIVED = "RECEIVED"
    STATUS_PROCESSED = "PROCESSED"
    STATUS_SKIPPED = "SKIPPED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = (
        (STATUS_RECEIVED, "Recebido"),
        (STATUS_PROCESSED, "Processado"),
        (STATUS_SKIPPED, "Ignorado"),
        (STATUS_FAILED, "Falhou"),
    )

    stripe_event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=128)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RECEIVED)
    payload = models.JSONField(default=dict, blank=True)
    processing_attempts = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    signature_verified = models.BooleanField(default=False)
    livemode = models.BooleanField(default=False)
    failure_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.stripe_event_id} - {self.status}"
