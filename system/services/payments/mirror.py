import logging

from django.apps import apps
from django.conf import settings

from system.services.payments.gateway import get_stripe_sdk


logger = logging.getLogger(__name__)


def is_djstripe_mirror_enabled():
    return bool(getattr(settings, "DJSTRIPE_ENABLED", False)) and apps.is_installed("djstripe")


def process_event_payload(event_payload):
    return _run_mirror_operation(
        label="event",
        operation=lambda: _get_djstripe_model("Event").process(data=event_payload),
        metadata={"event_id": event_payload.get("id"), "event_type": event_payload.get("type")},
    )


def sync_customer_payload(customer_payload):
    return _sync_payload(model_name="Customer", payload=customer_payload)


def sync_price_payload(price_payload):
    product_payload = price_payload.get("product")
    if isinstance(product_payload, dict):
        sync_product_payload(product_payload)
    return _sync_payload(model_name="Price", payload=price_payload)


def sync_product_payload(product_payload):
    return _sync_payload(model_name="Product", payload=product_payload)


def sync_subscription_payload(subscription_payload):
    return _sync_payload(model_name="Subscription", payload=subscription_payload)


def sync_invoice_payload(invoice_payload):
    return _sync_payload(model_name="Invoice", payload=invoice_payload)


def ensure_price_mirrored(stripe_price_id):
    return _ensure_object_mirrored(
        model_name="Price",
        stripe_id=stripe_price_id,
        retriever=lambda sdk, object_id: sdk.Price.retrieve(object_id, expand=["product"]),
        sync_callback=sync_price_payload,
    )


def ensure_subscription_mirrored(stripe_subscription_id):
    return _ensure_object_mirrored(
        model_name="Subscription",
        stripe_id=stripe_subscription_id,
        retriever=lambda sdk, object_id: sdk.Subscription.retrieve(object_id),
        sync_callback=sync_subscription_payload,
    )


def _sync_payload(*, model_name, payload):
    return _run_mirror_operation(
        label=model_name.lower(),
        operation=lambda: _get_djstripe_model(model_name).sync_from_stripe_data(payload),
        metadata={"stripe_id": payload.get("id")},
    )


def _ensure_object_mirrored(*, model_name, stripe_id, retriever, sync_callback):
    if not stripe_id:
        return None

    def operation():
        model_class = _get_djstripe_model(model_name)
        existing = model_class.objects.filter(id=stripe_id).first()
        if existing is not None:
            return existing
        sdk = get_stripe_sdk()
        payload = retriever(sdk, stripe_id)
        return sync_callback(payload)

    return _run_mirror_operation(
        label=model_name.lower(),
        operation=operation,
        metadata={"stripe_id": stripe_id},
    )


def _get_djstripe_model(model_name):
    return apps.get_model("djstripe", model_name)


def _run_mirror_operation(*, label, operation, metadata):
    if not is_djstripe_mirror_enabled():
        return None
    try:
        return operation()
    except Exception:
        logger.exception("djstripe_mirror_failed", extra={"label": label, "metadata": metadata})
        if getattr(settings, "DJSTRIPE_MIRROR_STRICT", False):
            raise
        return None
