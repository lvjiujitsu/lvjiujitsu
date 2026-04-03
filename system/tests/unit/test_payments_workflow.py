import json
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from system.models import CheckoutRequest, LocalSubscription, MonthlyInvoice, StripeSubscriptionLink
from system.services.finance import create_enrollment_pause, resume_enrollment_pause
from system.services.payments.checkout import resolve_current_price_map, start_subscription_checkout
from system.services.payments.webhooks import process_stripe_webhook
from system.tests.factories.finance_factories import LocalSubscriptionFactory, SubscriptionStudentFactory
from system.tests.factories.payments_factories import (
    StripeCustomerLinkFactory,
    StripePlanPriceMapFactory,
    StripeSubscriptionLinkFactory,
)


@pytest.mark.django_db
def test_resolve_current_price_map_requires_single_active_current_mapping():
    subscription = LocalSubscriptionFactory()
    current_map = StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)
    StripePlanPriceMapFactory(plan=subscription.plan, is_current=False, stripe_price_id="price_legacy")

    resolved = resolve_current_price_map(subscription.plan)

    assert resolved == current_map

    with transaction.atomic():
        with pytest.raises(IntegrityError):
            StripePlanPriceMapFactory(plan=subscription.plan, is_current=True, stripe_price_id="price_other")

    current_map.is_current = False
    current_map.save(update_fields=["is_current", "updated_at"])

    with pytest.raises(ValidationError):
        resolve_current_price_map(subscription.plan)


@pytest.mark.django_db
def test_start_subscription_checkout_creates_pending_request_and_preserves_local_pending(monkeypatch):
    subscription = LocalSubscriptionFactory(status=LocalSubscription.STATUS_ACTIVE)
    StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)

    monkeypatch.setattr(
        "system.services.payments.checkout.create_customer",
        lambda **kwargs: {"id": "cus_test_checkout", "livemode": False},
    )
    monkeypatch.setattr(
        "system.services.payments.checkout.create_checkout_session",
        lambda **kwargs: {"id": "cs_test_checkout", "url": "https://checkout.stripe.test/session"},
    )

    checkout_request = start_subscription_checkout(
        actor_user=subscription.responsible_user,
        local_subscription=subscription,
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )
    subscription.refresh_from_db()

    assert checkout_request.status == CheckoutRequest.STATUS_SESSION_CREATED
    assert checkout_request.checkout_url == "https://checkout.stripe.test/session"
    assert checkout_request.stripe_checkout_session_id == "cs_test_checkout"
    assert subscription.status == LocalSubscription.STATUS_PENDING_FINANCIAL


@pytest.mark.django_db
def test_start_subscription_checkout_failure_marks_request_failed_and_restores_local_status(monkeypatch):
    subscription = LocalSubscriptionFactory(status=LocalSubscription.STATUS_ACTIVE)
    StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)

    monkeypatch.setattr(
        "system.services.payments.checkout.create_customer",
        lambda **kwargs: {"id": "cus_test_checkout", "livemode": False},
    )

    def raise_checkout_error(**kwargs):
        raise RuntimeError("Stripe indisponivel")

    monkeypatch.setattr("system.services.payments.checkout.create_checkout_session", raise_checkout_error)

    with pytest.raises(RuntimeError):
        start_subscription_checkout(
            actor_user=subscription.responsible_user,
            local_subscription=subscription,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

    checkout_request = subscription.checkout_requests.get()
    subscription.refresh_from_db()

    assert checkout_request.status == CheckoutRequest.STATUS_FAILED
    assert "Stripe indisponivel" in checkout_request.failure_message
    assert subscription.status == LocalSubscription.STATUS_ACTIVE


@pytest.mark.django_db
def test_process_stripe_webhook_is_idempotent_and_marks_invoice_paid():
    subscription = LocalSubscriptionFactory(status=LocalSubscription.STATUS_PENDING_FINANCIAL)
    price_map = StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)
    customer_link = StripeCustomerLinkFactory(user=subscription.responsible_user)
    StripeSubscriptionLinkFactory(
        local_subscription=subscription,
        customer_link=customer_link,
        price_map=price_map,
        stripe_subscription_id="sub_webhook_paid",
        stripe_status=StripeSubscriptionLink.STATUS_PENDING,
    )
    created_at = int(timezone.now().timestamp())
    event = {
        "id": "evt_invoice_paid_001",
        "type": "invoice.paid",
        "livemode": False,
        "data": {
            "object": {
                "id": "in_test_paid",
                "subscription": "sub_webhook_paid",
                "total": 25000,
                "subtotal": 25000,
                "created": created_at,
                "period_start": created_at,
                "due_date": created_at + 86400,
            }
        },
    }

    processing, duplicate = process_stripe_webhook(
        payload=json.dumps(event).encode("utf-8"),
        signature="",
    )
    second_processing, second_duplicate = process_stripe_webhook(
        payload=json.dumps(event).encode("utf-8"),
        signature="",
    )
    subscription.refresh_from_db()
    invoice = MonthlyInvoice.objects.get(subscription=subscription)

    assert processing.status == "PROCESSED"
    assert duplicate is False
    assert second_processing.pk == processing.pk
    assert second_duplicate is True
    assert invoice.status == MonthlyInvoice.STATUS_PAID
    assert subscription.status == LocalSubscription.STATUS_ACTIVE


@pytest.mark.django_db
def test_process_stripe_webhook_attempts_djstripe_mirror_before_local_dispatch(monkeypatch):
    mirror_calls = []
    event = {
        "id": "evt_customer_created_001",
        "type": "customer.created",
        "livemode": False,
        "data": {"object": {"id": "cus_test_created", "object": "customer"}},
    }

    monkeypatch.setattr(
        "system.services.payments.webhooks.process_event_payload",
        lambda payload: mirror_calls.append(payload) or None,
    )

    processing, duplicate = process_stripe_webhook(
        payload=json.dumps(event).encode("utf-8"),
        signature="",
    )

    assert duplicate is False
    assert processing.status == "PROCESSED"
    assert mirror_calls == [event]


@pytest.mark.django_db(transaction=True)
def test_pause_and_resume_linked_subscription_collection_updates_stripe_link(monkeypatch):
    pause_calls = []
    resume_calls = []
    subscription = LocalSubscriptionFactory()
    price_map = StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)
    StripeSubscriptionLinkFactory(
        local_subscription=subscription,
        customer_link=StripeCustomerLinkFactory(user=subscription.responsible_user),
        price_map=price_map,
        stripe_subscription_id="sub_pause_test",
        stripe_status=StripeSubscriptionLink.STATUS_ACTIVE,
    )
    covered_student = SubscriptionStudentFactory(subscription=subscription).student

    monkeypatch.setattr(
        "system.services.payments.subscriptions.pause_subscription_collection",
        lambda **kwargs: pause_calls.append(kwargs) or {"id": "sub_pause_test", "pause_collection": kwargs},
    )
    monkeypatch.setattr(
        "system.services.payments.subscriptions.resume_subscription_collection",
        lambda **kwargs: resume_calls.append(kwargs) or {"id": "sub_pause_test", "pause_collection": ""},
    )

    pause = create_enrollment_pause(
        student=covered_student,
        subscription=subscription,
        reason="Lesao",
        start_date=timezone.localdate(),
        expected_return_date=timezone.localdate() + timedelta(days=10),
    )
    link = subscription.stripe_subscription_link
    link.refresh_from_db()

    assert pause_calls
    assert link.stripe_status == StripeSubscriptionLink.STATUS_PAUSED_COLLECTION
    assert link.pause_collection_resumes_at is not None

    resume_enrollment_pause(pause)
    link.refresh_from_db()

    assert resume_calls
    assert link.stripe_status == StripeSubscriptionLink.STATUS_ACTIVE
