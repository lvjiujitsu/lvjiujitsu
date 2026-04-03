from datetime import datetime, time

from django.conf import settings
from django.utils import timezone

from system.models import StripeSubscriptionLink
from system.services.payments.gateway import (
    normalize_stripe_payload,
    pause_subscription_collection,
    resume_subscription_collection,
)


def pause_linked_subscription_collection(*, local_subscription, pause):
    link = getattr(local_subscription, "stripe_subscription_link", None)
    if link is None or not link.price_map or not link.price_map.supports_pause_collection:
        return None
    response = normalize_stripe_payload(
        pause_subscription_collection(
            stripe_subscription_id=link.stripe_subscription_id,
            behavior=settings.STRIPE_PAUSE_COLLECTION_BEHAVIOR,
            resumes_at=_resolve_pause_return(pause),
        )
    )
    link.stripe_status = StripeSubscriptionLink.STATUS_PAUSED_COLLECTION
    link.pause_collection_behavior = settings.STRIPE_PAUSE_COLLECTION_BEHAVIOR
    link.pause_collection_resumes_at = _resolve_pause_resume_datetime(pause)
    link.latest_payload = response
    link.save(
        update_fields=[
            "stripe_status",
            "pause_collection_behavior",
            "pause_collection_resumes_at",
            "latest_payload",
            "updated_at",
        ]
    )
    return link


def resume_linked_subscription_collection(*, local_subscription):
    link = getattr(local_subscription, "stripe_subscription_link", None)
    if link is None:
        return None
    response = normalize_stripe_payload(
        resume_subscription_collection(stripe_subscription_id=link.stripe_subscription_id)
    )
    link.stripe_status = StripeSubscriptionLink.STATUS_ACTIVE
    link.pause_collection_behavior = ""
    link.pause_collection_resumes_at = None
    link.latest_payload = response
    link.save(
        update_fields=[
            "stripe_status",
            "pause_collection_behavior",
            "pause_collection_resumes_at",
            "latest_payload",
            "updated_at",
        ]
    )
    return link


def _resolve_pause_return(pause):
    if not pause.expected_return_date:
        return None
    return _resolve_pause_resume_datetime(pause)


def _resolve_pause_resume_datetime(pause):
    if not pause.expected_return_date:
        return None
    naive_value = datetime.combine(pause.expected_return_date, time.min)
    return timezone.make_aware(naive_value, timezone.get_current_timezone())
