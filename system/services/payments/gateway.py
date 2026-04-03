from datetime import date, datetime
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def normalize_stripe_payload(payload):
    if hasattr(payload, "to_dict_recursive"):
        payload = payload.to_dict_recursive()
    if isinstance(payload, dict):
        return {key: normalize_stripe_payload(value) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [normalize_stripe_payload(item) for item in payload]
    if isinstance(payload, (datetime, date)):
        return payload.isoformat()
    if isinstance(payload, Decimal):
        return str(payload)
    return payload


def is_stripe_configured():
    return bool(settings.STRIPE_SECRET_KEY)


def get_stripe_sdk():
    if not is_stripe_configured():
        raise ImproperlyConfigured("STRIPE_SECRET_KEY nao configurada.")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.api_version = settings.STRIPE_API_VERSION
    stripe.max_network_retries = 2
    return stripe


def create_customer(*, name, email, metadata):
    sdk = get_stripe_sdk()
    return sdk.Customer.create(name=name, email=email or None, metadata=metadata)


def create_checkout_session(*, customer_id, price_id, success_url, cancel_url, metadata):
    sdk = get_stripe_sdk()
    return sdk.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=metadata["local_subscription_uuid"],
        metadata=metadata,
        subscription_data={"metadata": metadata},
    )


def create_billing_portal_session(*, customer_id, return_url):
    sdk = get_stripe_sdk()
    return sdk.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def pause_subscription_collection(*, stripe_subscription_id, behavior, resumes_at=None):
    sdk = get_stripe_sdk()
    pause_collection = {"behavior": behavior}
    if resumes_at:
        pause_collection["resumes_at"] = int(resumes_at.timestamp())
    return sdk.Subscription.modify(
        stripe_subscription_id,
        pause_collection=pause_collection,
    )


def resume_subscription_collection(*, stripe_subscription_id):
    sdk = get_stripe_sdk()
    return sdk.Subscription.modify(stripe_subscription_id, pause_collection="")


def construct_event(*, payload, signature):
    sdk = get_stripe_sdk()
    return sdk.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=settings.STRIPE_WEBHOOK_SECRET,
    )
