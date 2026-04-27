from django.db import models
from django.db.models import Q

from .common import TimeStampedModel


class ProductBackorderStatus(models.TextChoices):
    PENDING = "pending", "Aguardando estoque"
    READY = "ready", "Estoque chegou"
    CONFIRMED = "confirmed", "Confirmado e pago"
    CANCELED = "canceled", "Cancelado"
    EXPIRED = "expired", "Reserva expirada"


ACTIVE_BACKORDER_STATUSES = (
    ProductBackorderStatus.PENDING,
    ProductBackorderStatus.READY,
)


class ProductBackorder(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="product_backorders",
        verbose_name="Pessoa",
    )
    variant = models.ForeignKey(
        "system.ProductVariant",
        on_delete=models.PROTECT,
        related_name="backorders",
        verbose_name="Variante",
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=ProductBackorderStatus.choices,
        default=ProductBackorderStatus.PENDING,
    )
    notified_at = models.DateTimeField(
        "Notificado em",
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(
        "Confirmado em",
        null=True,
        blank=True,
    )
    canceled_at = models.DateTimeField(
        "Cancelado em",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(
        "Expira em",
        null=True,
        blank=True,
    )
    confirmed_order = models.ForeignKey(
        "system.RegistrationOrder",
        on_delete=models.SET_NULL,
        related_name="product_backorders",
        null=True,
        blank=True,
        verbose_name="Pedido confirmado",
    )
    notes = models.TextField("Observações", blank=True, default="")

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Pré-pedido de produto"
        verbose_name_plural = "Pré-pedidos de produtos"
        constraints = [
            models.UniqueConstraint(
                fields=("person", "variant"),
                condition=Q(status__in=("pending", "ready")),
                name="unique_active_product_backorder",
            ),
        ]
        indexes = [
            models.Index(fields=("variant", "status", "created_at")),
            models.Index(fields=("person", "status")),
        ]

    def __str__(self):
        return f"Backorder #{self.pk} — {self.person.full_name} → {self.variant}"

    @property
    def is_active(self):
        return self.status in ACTIVE_BACKORDER_STATUSES

    @property
    def is_ready(self):
        return self.status == ProductBackorderStatus.READY
