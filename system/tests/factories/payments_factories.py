from decimal import Decimal

import factory

from system.models import CheckoutRequest, StripeCustomerLink, StripePlanPriceMap, StripeSubscriptionLink, WebhookProcessing
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.finance_factories import FinancialPlanFactory, LocalSubscriptionFactory


class StripeCustomerLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StripeCustomerLink

    user = factory.SubFactory(SystemUserFactory)
    stripe_customer_id = factory.Sequence(lambda index: f"cus_test_{index}")
    livemode = False
    metadata = factory.LazyAttribute(lambda obj: {"cpf": obj.user.cpf})


class StripePlanPriceMapFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StripePlanPriceMap

    plan = factory.SubFactory(FinancialPlanFactory)
    stripe_product_id = factory.Sequence(lambda index: f"prod_test_{index}")
    stripe_price_id = factory.Sequence(lambda index: f"price_test_{index}")
    product_name = factory.Sequence(lambda index: f"Produto Stripe {index}")
    currency = "brl"
    amount = Decimal("250.00")
    recurring_interval = "month"
    recurring_interval_count = 1
    is_active = True
    is_current = False


class StripeSubscriptionLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StripeSubscriptionLink

    local_subscription = factory.SubFactory(LocalSubscriptionFactory)
    customer_link = factory.SubFactory(
        StripeCustomerLinkFactory,
        user=factory.SelfAttribute("..local_subscription.responsible_user"),
    )
    price_map = factory.SubFactory(
        StripePlanPriceMapFactory,
        plan=factory.SelfAttribute("..local_subscription.plan"),
    )
    stripe_subscription_id = factory.Sequence(lambda index: f"sub_test_{index}")
    stripe_status = StripeSubscriptionLink.STATUS_PENDING


class CheckoutRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CheckoutRequest

    requester = factory.SubFactory(SystemUserFactory)
    local_subscription = factory.SubFactory(LocalSubscriptionFactory)
    customer_link = factory.SubFactory(
        StripeCustomerLinkFactory,
        user=factory.SelfAttribute("..local_subscription.responsible_user"),
    )
    price_map = factory.SubFactory(
        StripePlanPriceMapFactory,
        plan=factory.SelfAttribute("..local_subscription.plan"),
    )
    success_url = "https://example.com/success"
    cancel_url = "https://example.com/cancel"


class WebhookProcessingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookProcessing

    stripe_event_id = factory.Sequence(lambda index: f"evt_test_{index}")
    event_type = "invoice.paid"
    status = WebhookProcessing.STATUS_RECEIVED
