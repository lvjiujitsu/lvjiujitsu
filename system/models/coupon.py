from decimal import Decimal

from django.db import models

from .common import TimeStampedModel


class DiscountType(models.TextChoices):
    PERCENT = "percent", "Percentual (%)"
    FIXED = "fixed", "Valor fixo (R$)"


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        default=DiscountType.PERCENT,
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cupom de desconto"
        verbose_name_plural = "Cupons de desconto"
        ordering = ["code"]

    def __str__(self):
        return self.code

    def apply_to(self, total):
        total = Decimal(str(total))
        if self.discount_type == DiscountType.PERCENT:
            discount = (total * self.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            discount = self.discount_value.quantize(Decimal("0.01"))
        discount = min(discount, total)
        discounted = (total - discount).quantize(Decimal("0.01"))
        return max(discounted, Decimal("0.00")), discount
