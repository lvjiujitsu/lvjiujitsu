import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from system.business_rule.models.product import ProductVariant
from system.business_rule.services.product_backorders import restock_variant
from system.business_rule.services.product_backorders import cancel_all_active_for_variant


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ProductVariant)
def capture_product_variant_stock_delta(sender, instance, **kwargs):
    if instance.pk is None:
        instance._stock_delta = instance.stock_quantity if instance.is_active else 0
        instance._was_active = False
        return
    try:
        previous = ProductVariant.objects.only("stock_quantity", "is_active").get(pk=instance.pk)
    except ProductVariant.DoesNotExist:
        instance._stock_delta = 0
        instance._was_active = False
        return
    instance._stock_delta = max(0, instance.stock_quantity - previous.stock_quantity)
    instance._was_active = previous.is_active


@receiver(post_save, sender=ProductVariant)
def promote_backorders_on_restock(sender, instance, created, **kwargs):
    delta = getattr(instance, "_stock_delta", 0)
    was_active = getattr(instance, "_was_active", False)

    if instance.is_active and delta > 0:
        try:
            restock_variant(instance, delta)
        except Exception:
            logger.exception(
                "Falha ao promover pré-pedidos da variante %s", instance.pk
            )

    if was_active and not instance.is_active:
        try:
            cancel_all_active_for_variant(
                instance,
                reason="Variante desativada — pré-pedido cancelado automaticamente.",
            )
        except Exception:
            logger.exception(
                "Falha ao cancelar pré-pedidos da variante desativada %s", instance.pk
            )
