from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO
from system.models import (
    CheckoutRequest,
    LocalSubscription,
    StripeCustomerLink,
    StripePlanPriceMap,
    StripeSubscriptionLink,
)
from system.services.finance import sync_subscription_status
from system.services.payments.gateway import (
    create_billing_portal_session,
    create_checkout_session,
    create_customer,
    normalize_stripe_payload,
)
from system.services.payments.mirror import (
    ensure_price_mirrored,
    ensure_subscription_mirrored,
    sync_customer_payload,
)


def resolve_current_price_map(plan):
    queryset = StripePlanPriceMap.objects.filter(plan=plan, is_active=True, is_current=True)
    count = queryset.count()
    if count != 1:
        raise ValidationError("Existe ambiguidade ou ausencia de Price Stripe vigente para este plano.")
    return queryset.select_related("plan").get()


@transaction.atomic
def ensure_stripe_customer_link(user):
    existing = getattr(user, "stripe_customer_link", None)
    if existing:
        return existing
    metadata = {
        "user_uuid": str(user.uuid),
        "cpf": user.cpf,
    }
    customer = normalize_stripe_payload(
        create_customer(name=user.full_name, email=user.email, metadata=metadata)
    )
    sync_customer_payload(customer)
    return StripeCustomerLink.objects.create(
        user=user,
        stripe_customer_id=customer["id"],
        livemode=bool(customer.get("livemode", False)),
        metadata=metadata,
        last_synced_at=timezone.now(),
    )


def start_subscription_checkout(*, actor_user, local_subscription, success_url, cancel_url):
    _validate_checkout_eligibility(local_subscription, actor_user)
    price_map = resolve_current_price_map(local_subscription.plan)
    ensure_price_mirrored(price_map.stripe_price_id)
    customer_link = ensure_stripe_customer_link(local_subscription.responsible_user)
    metadata = _build_checkout_metadata(local_subscription)
    with transaction.atomic():
        checkout_request = CheckoutRequest.objects.create(
            requester=actor_user,
            local_subscription=local_subscription,
            customer_link=customer_link,
            price_map=price_map,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata_snapshot=metadata,
        )
        _mark_local_subscription_pending(local_subscription)
    metadata["checkout_request_uuid"] = str(checkout_request.uuid)
    try:
        session = normalize_stripe_payload(
            create_checkout_session(
                customer_id=customer_link.stripe_customer_id,
                price_id=price_map.stripe_price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
        )
    except Exception as exc:
        _mark_checkout_request_failed(checkout_request, local_subscription, failure_message=str(exc))
        raise
    with transaction.atomic():
        checkout_request.status = CheckoutRequest.STATUS_SESSION_CREATED
        checkout_request.stripe_checkout_session_id = session["id"]
        checkout_request.checkout_url = session["url"]
        checkout_request.metadata_snapshot = metadata
        checkout_request.failure_message = ""
        checkout_request.failed_at = None
        checkout_request.save(
            update_fields=[
                "status",
                "stripe_checkout_session_id",
                "checkout_url",
                "metadata_snapshot",
                "failure_message",
                "failed_at",
                "updated_at",
            ]
        )
    return checkout_request


def create_customer_portal(*, local_subscription, return_url):
    customer_link = ensure_stripe_customer_link(local_subscription.responsible_user)
    return normalize_stripe_payload(
        create_billing_portal_session(
            customer_id=customer_link.stripe_customer_id,
            return_url=return_url,
        )
    )


@transaction.atomic
def record_checkout_completion(session_payload):
    session_payload = normalize_stripe_payload(session_payload)
    checkout_request = _resolve_checkout_request(session_payload)
    if checkout_request.status == CheckoutRequest.STATUS_COMPLETED:
        return checkout_request
    customer_link = ensure_stripe_customer_link(checkout_request.local_subscription.responsible_user)
    stripe_subscription_id = session_payload.get("subscription") or None
    if stripe_subscription_id:
        StripeSubscriptionLink.objects.update_or_create(
            local_subscription=checkout_request.local_subscription,
            defaults={
                "customer_link": customer_link,
                "price_map": checkout_request.price_map,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_status": StripeSubscriptionLink.STATUS_PENDING,
                "livemode": bool(session_payload.get("livemode", False)),
                "latest_payload": session_payload,
            },
        )
        ensure_subscription_mirrored(stripe_subscription_id)
    checkout_request.customer_link = customer_link
    checkout_request.status = CheckoutRequest.STATUS_COMPLETED
    checkout_request.stripe_subscription_id = stripe_subscription_id
    checkout_request.completed_at = timezone.now()
    checkout_request.save(
        update_fields=[
            "customer_link",
            "status",
            "stripe_subscription_id",
            "completed_at",
            "updated_at",
        ]
    )
    _mark_local_subscription_pending(checkout_request.local_subscription)
    return checkout_request


@transaction.atomic
def expire_checkout_request(session_payload):
    session_payload = normalize_stripe_payload(session_payload)
    checkout_request = _resolve_checkout_request(session_payload)
    if checkout_request.status in {CheckoutRequest.STATUS_COMPLETED, CheckoutRequest.STATUS_EXPIRED}:
        return checkout_request
    checkout_request.status = CheckoutRequest.STATUS_EXPIRED
    checkout_request.failure_message = "Sessao de checkout expirada na Stripe."
    checkout_request.failed_at = timezone.now()
    checkout_request.save(update_fields=["status", "failure_message", "failed_at", "updated_at"])
    sync_subscription_status(checkout_request.local_subscription)
    return checkout_request


def _validate_checkout_eligibility(local_subscription, actor_user):
    if actor_user != local_subscription.responsible_user and not actor_user.is_superuser:
        if not actor_user.has_any_role(ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO):
            raise ValidationError("Voce nao pode iniciar checkout para este contrato.")
    if local_subscription.status == LocalSubscription.STATUS_CANCELLED:
        raise ValidationError("Nao e permitido iniciar checkout para contrato cancelado.")
    if local_subscription.checkout_requests.filter(
        status__in=(CheckoutRequest.STATUS_CREATED, CheckoutRequest.STATUS_SESSION_CREATED)
    ).exists():
        raise ValidationError("Ja existe um checkout em andamento para este contrato.")
    external_link = getattr(local_subscription, "stripe_subscription_link", None)
    if external_link and external_link.stripe_status in {
        StripeSubscriptionLink.STATUS_ACTIVE,
        StripeSubscriptionLink.STATUS_PAUSED_COLLECTION,
        StripeSubscriptionLink.STATUS_PENDING,
    }:
        raise ValidationError("Este contrato ja possui assinatura Stripe vinculada.")


def _build_checkout_metadata(local_subscription):
    student_uuids = list(local_subscription.covered_students.values_list("student__uuid", flat=True))
    return {
        "local_subscription_uuid": str(local_subscription.uuid),
        "plan_uuid": str(local_subscription.plan.uuid),
        "responsible_user_uuid": str(local_subscription.responsible_user.uuid),
        "student_uuids": ",".join(str(item) for item in student_uuids),
    }


def _resolve_checkout_request(session_payload):
    session_id = session_payload.get("id")
    metadata = session_payload.get("metadata") or {}
    checkout_request_uuid = metadata.get("checkout_request_uuid")
    queryset = CheckoutRequest.objects.select_related("local_subscription", "price_map")
    if session_id:
        checkout_request = queryset.filter(stripe_checkout_session_id=session_id).first()
        if checkout_request:
            return checkout_request
    if checkout_request_uuid:
        checkout_request = queryset.filter(uuid=checkout_request_uuid).first()
        if checkout_request:
            return checkout_request
    raise ValidationError("Checkout local nao encontrado para a sessao Stripe.")


def _mark_local_subscription_pending(local_subscription):
    local_subscription.status = LocalSubscription.STATUS_PENDING_FINANCIAL
    local_subscription.save(update_fields=["status", "updated_at"])


@transaction.atomic
def _mark_checkout_request_failed(checkout_request, local_subscription, *, failure_message):
    checkout_request.status = CheckoutRequest.STATUS_FAILED
    checkout_request.failure_message = failure_message
    checkout_request.failed_at = timezone.now()
    checkout_request.save(update_fields=["status", "failure_message", "failed_at", "updated_at"])
    sync_subscription_status(local_subscription)
