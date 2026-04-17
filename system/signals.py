import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from system.models.plan import PlanPaymentMethod, SubscriptionPlan
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
