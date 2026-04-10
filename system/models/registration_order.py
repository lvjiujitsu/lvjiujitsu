from django.db import models

from .common import TimeStampedModel


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

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Pedido de matrícula"
        verbose_name_plural = "Pedidos de matrícula"

    def __str__(self):
        return f"Pedido #{self.pk} — {self.person.full_name}"


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
