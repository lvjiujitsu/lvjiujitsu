from django.core.validators import MinValueValidator
from django.db import models

from .common import TimeStampedModel


class ProductCategory(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=120)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "display_name")
        verbose_name = "Categoria de produto"
        verbose_name_plural = "Categorias de produto"

    def __str__(self):
        return self.display_name


class Product(TimeStampedModel):
    sku = models.CharField("SKU", max_length=60, unique=True)
    display_name = models.CharField("Nome", max_length=200)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Categoria",
    )
    unit_price = models.DecimalField(
        "Preço unitário",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    description = models.TextField("Descrição", blank=True, default="")
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ("category__display_order", "display_name")
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.display_name

    @property
    def total_stock(self):
        if hasattr(self, "_total_stock"):
            return self._total_stock or 0
        return (
            self.variants.filter(is_active=True)
            .aggregate(total=models.Sum("stock_quantity"))["total"]
            or 0
        )

    @property
    def variant_count(self):
        if hasattr(self, "_variant_count"):
            return self._variant_count or 0
        return self.variants.filter(is_active=True).count()

    @property
    def is_in_stock(self):
        return self.total_stock > 0


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="Produto",
    )
    size = models.CharField("Tamanho", max_length=20, blank=True, default="")
    color = models.CharField("Cor", max_length=60, blank=True, default="")
    stock_quantity = models.PositiveIntegerField("Estoque", default=0)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ("color", "size")
        verbose_name = "Variante de produto"
        verbose_name_plural = "Variantes de produto"
        constraints = [
            models.UniqueConstraint(
                fields=("product", "size", "color"),
                name="unique_product_variant",
            ),
        ]

    def __str__(self):
        parts = [self.product.display_name]
        if self.color:
            parts.append(self.color)
        if self.size:
            parts.append(self.size)
        return " — ".join(parts)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
