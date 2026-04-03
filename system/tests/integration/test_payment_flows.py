import json

import pytest
from django.urls import reverse
from django.utils import timezone

from system.models import CheckoutRequest, MonthlyInvoice
from system.tests.factories.auth_factories import AdminUserFactory, SystemUserFactory
from system.tests.factories.finance_factories import LocalSubscriptionFactory
from system.tests.factories.payments_factories import (
    StripeCustomerLinkFactory,
    StripePlanPriceMapFactory,
    StripeSubscriptionLinkFactory,
)


@pytest.mark.django_db
def test_responsible_user_can_start_subscription_checkout_flow(client, monkeypatch, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_local"
    responsible_user = SystemUserFactory(password="StrongPassword123")
    subscription = LocalSubscriptionFactory(responsible_user=responsible_user)
    StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)

    monkeypatch.setattr(
        "system.services.payments.checkout.create_customer",
        lambda **kwargs: {"id": "cus_test_checkout", "livemode": False},
    )
    monkeypatch.setattr(
        "system.services.payments.checkout.create_checkout_session",
        lambda **kwargs: {"id": "cs_test_checkout", "url": "https://checkout.stripe.test/session"},
    )
    client.force_login(responsible_user)

    response = client.post(
        reverse("system:subscription-checkout-start", kwargs={"uuid": subscription.uuid}),
        data={"next": reverse("system:my-invoices")},
    )

    subscription.refresh_from_db()
    checkout_request = CheckoutRequest.objects.get(local_subscription=subscription)

    assert response.status_code == 302
    assert response.url == "https://checkout.stripe.test/session"
    assert checkout_request.status == CheckoutRequest.STATUS_SESSION_CREATED
    assert subscription.status == subscription.STATUS_PENDING_FINANCIAL


@pytest.mark.django_db
def test_non_owner_cannot_start_checkout_for_foreign_contract(client, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_local"
    owner = SystemUserFactory(password="StrongPassword123")
    other_user = SystemUserFactory(password="StrongPassword123")
    subscription = LocalSubscriptionFactory(responsible_user=owner)
    StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)
    client.force_login(other_user)

    response = client.post(
        reverse("system:subscription-checkout-start", kwargs={"uuid": subscription.uuid}),
        data={"next": reverse("system:my-invoices")},
    )

    assert response.status_code == 404
    assert CheckoutRequest.objects.count() == 0


@pytest.mark.django_db
def test_responsible_user_can_open_customer_portal(client, monkeypatch, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_local"
    responsible_user = SystemUserFactory(password="StrongPassword123")
    subscription = LocalSubscriptionFactory(responsible_user=responsible_user)
    StripeCustomerLinkFactory(user=responsible_user)

    monkeypatch.setattr(
        "system.services.payments.checkout.create_billing_portal_session",
        lambda **kwargs: {"url": "https://billing.stripe.test/session"},
    )
    client.force_login(responsible_user)

    response = client.post(
        reverse("system:customer-portal-start", kwargs={"uuid": subscription.uuid}),
        data={"next": reverse("system:my-invoices")},
    )

    assert response.status_code == 302
    assert response.url == "https://billing.stripe.test/session"


@pytest.mark.django_db
def test_non_owner_cannot_open_customer_portal_for_foreign_contract(client, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_local"
    owner = SystemUserFactory(password="StrongPassword123")
    other_user = SystemUserFactory(password="StrongPassword123")
    subscription = LocalSubscriptionFactory(responsible_user=owner)
    StripeCustomerLinkFactory(user=owner)
    client.force_login(other_user)

    response = client.post(
        reverse("system:customer-portal-start", kwargs={"uuid": subscription.uuid}),
        data={"next": reverse("system:my-invoices")},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_webhook_endpoint_is_idempotent_for_invoice_paid(client):
    subscription = LocalSubscriptionFactory(status=LocalSubscriptionFactory._meta.model.STATUS_PENDING_FINANCIAL)
    price_map = StripePlanPriceMapFactory(plan=subscription.plan, is_current=True)
    customer_link = StripeCustomerLinkFactory(user=subscription.responsible_user)
    StripeSubscriptionLinkFactory(
        local_subscription=subscription,
        customer_link=customer_link,
        price_map=price_map,
        stripe_subscription_id="sub_http_webhook",
    )
    created_at = int(timezone.now().timestamp())
    payload = {
        "id": "evt_invoice_paid_http",
        "type": "invoice.paid",
        "livemode": False,
        "data": {
            "object": {
                "id": "in_http_paid",
                "subscription": "sub_http_webhook",
                "total": 25000,
                "subtotal": 25000,
                "created": created_at,
                "period_start": created_at,
                "due_date": created_at + 86400,
            }
        },
    }

    first_response = client.post(
        reverse("system:stripe-webhook"),
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="",
    )
    second_response = client.post(
        reverse("system:stripe-webhook"),
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="",
    )
    subscription.refresh_from_db()
    invoice = MonthlyInvoice.objects.get(subscription=subscription)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert MonthlyInvoice.objects.count() == 1
    assert invoice.status == MonthlyInvoice.STATUS_PAID
    assert subscription.status == subscription.STATUS_ACTIVE
