from django.db.models import Prefetch, Q

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.models import CheckoutRequest, LocalSubscription, StripePlanPriceMap, StripeSubscriptionLink, WebhookProcessing


def get_stripe_price_maps_queryset():
    return StripePlanPriceMap.objects.select_related("plan").order_by("plan__name", "-is_current", "-valid_from")


def get_checkout_requests_queryset():
    return CheckoutRequest.objects.select_related(
        "requester",
        "local_subscription",
        "local_subscription__responsible_user",
        "local_subscription__plan",
        "price_map",
    ).order_by("-created_at")


def get_stripe_subscription_links_queryset():
    return StripeSubscriptionLink.objects.select_related(
        "local_subscription",
        "local_subscription__responsible_user",
        "local_subscription__plan",
        "customer_link",
        "price_map",
    ).order_by("-created_at")


def get_webhook_processing_queryset():
    return WebhookProcessing.objects.order_by("-created_at")


def get_checkout_allowed_subscriptions(user):
    checkout_requests = CheckoutRequest.objects.select_related("price_map").order_by("-created_at")
    queryset = (
        LocalSubscription.objects.select_related(
            "plan",
            "responsible_user",
            "stripe_subscription_link",
            "stripe_subscription_link__price_map",
        )
        .prefetch_related(Prefetch("checkout_requests", queryset=checkout_requests))
    )
    if _is_staff_operator(user):
        return queryset.exclude(status=LocalSubscription.STATUS_CANCELLED).order_by("-created_at")
    return queryset.filter(
        Q(responsible_user=user),
    ).exclude(status=LocalSubscription.STATUS_CANCELLED).order_by("-created_at")


def _is_staff_operator(user):
    return user.is_superuser or user.has_any_role(
        ROLE_ADMIN_MASTER,
        ROLE_ADMIN_UNIDADE,
        ROLE_RECEPCAO,
    )
