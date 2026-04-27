import logging

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from system.models.plan import PlanPaymentMethod, SubscriptionPlan
from system.models.product import ProductVariant
from system.services.stripe_sync import StripeSyncError, sync_plan_to_stripe


logger = logging.getLogger(__name__)


@receiver(post_save, sender=SubscriptionPlan)
def sync_subscription_plan_to_stripe(sender, instance, created, **kwargs):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PLAN_SYNC_ENABLED:
        return
    if instance.payment_method != PlanPaymentMethod.CREDIT_CARD:
        return
    if kwargs.get("update_fields"):
        tracked = {
            "display_name",
            "description",
            "price",
            "billing_cycle",
            "payment_method",
            "is_active",
        }
        if not set(kwargs["update_fields"]) & tracked:
            return
    try:
        sync_plan_to_stripe(instance)
    except StripeSyncError as exc:
        logger.warning(
            "Falha silenciosa ao sincronizar plano %s com Stripe: %s", instance.pk, exc
        )
    except Exception:
        logger.exception(
            "Erro inesperado ao sincronizar plano %s com Stripe", instance.pk
        )


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
        from system.services.product_backorders import restock_variant
        try:
            restock_variant(instance, delta)
        except Exception:
            logger.exception(
                "Falha ao promover pré-pedidos da variante %s", instance.pk
            )

    if was_active and not instance.is_active:
        from system.services.product_backorders import cancel_all_active_for_variant
        try:
            cancel_all_active_for_variant(
                instance,
                reason="Variante desativada — pré-pedido cancelado automaticamente.",
            )
        except Exception:
            logger.exception(
                "Falha ao cancelar pré-pedidos da variante desativada %s", instance.pk
            )
