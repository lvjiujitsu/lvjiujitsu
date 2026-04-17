import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.models.membership import Membership, MembershipStatus
from system.models.plan import SubscriptionPlan
from system.models.registration_order import PaymentStatus, RegistrationOrder


logger = logging.getLogger(__name__)


class StripeAdminActionError(Exception):
    pass


def _get_client():
    if not settings.STRIPE_SECRET_KEY:
        raise StripeAdminActionError("STRIPE_SECRET_KEY não configurada no .env")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _to_cents(value):
    return int((Decimal(value) * 100).quantize(Decimal("1")))


@transaction.atomic
def cancel_membership(membership, *, at_period_end=True, admin_user=None, reason=""):
    client = _get_client()
    if not membership.stripe_subscription_id:
        membership.status = MembershipStatus.CANCELED
        membership.canceled_at = timezone.now()
        membership.cancel_at_period_end = False
        membership.notes = (membership.notes + "\n" + reason).strip() if reason else membership.notes
        membership.save(
            update_fields=["status", "canceled_at", "cancel_at_period_end", "notes", "updated_at"]
        )
        return membership

    try:
        if at_period_end:
            client.Subscription.modify(
                membership.stripe_subscription_id,
                cancel_at_period_end=True,
                metadata={
                    "canceled_by_admin": str(getattr(admin_user, "pk", "")),
                    "cancel_reason": reason[:200],
                },
            )
            membership.cancel_at_period_end = True
        else:
            client.Subscription.delete(
                membership.stripe_subscription_id,
                prorate=True,
            )
            membership.status = MembershipStatus.CANCELED
            membership.canceled_at = timezone.now()
            membership.cancel_at_period_end = False
    except Exception as exc:
        logger.exception("Falha ao cancelar assinatura %s", membership.pk)
        raise StripeAdminActionError(str(exc)) from exc

    if reason:
        membership.notes = (membership.notes + "\n" + reason).strip()
    membership.save()
    return membership


@transaction.atomic
def refund_order(order, *, amount=None, admin_user=None, reason=""):
    client = _get_client()
    if not order.stripe_payment_intent_id:
        raise StripeAdminActionError(
            "Pedido sem PaymentIntent Stripe — não é possível estornar."
        )

    try:
        params = {"payment_intent": order.stripe_payment_intent_id}
        if amount is not None:
            params["amount"] = _to_cents(amount)
        if reason:
            params["metadata"] = {"admin_reason": reason[:200]}
        refund = client.Refund.create(**params)
    except Exception as exc:
        logger.exception("Falha ao estornar pedido %s", order.pk)
        raise StripeAdminActionError(str(exc)) from exc

    refunded_amount = Decimal(refund["amount"] if "amount" in refund else 0) / Decimal("100")
    order.refunded_at = timezone.now()
    if amount is None or refunded_amount >= (order.total or Decimal("0")):
        order.payment_status = PaymentStatus.REFUNDED
    if reason:
        order.notes = (order.notes + "\n" + f"Estorno: {reason}").strip()
    order.save(update_fields=["refunded_at", "payment_status", "notes", "updated_at"])
    return {"refund_id": refund["id"], "amount": refunded_amount, "order": order}


@transaction.atomic
def change_membership_plan(membership, new_plan, *, admin_user=None):
    client = _get_client()
    if not membership.stripe_subscription_id:
        raise StripeAdminActionError(
            "Assinatura sem Subscription Stripe — use 'troca manual' em vez disso."
        )
    if not new_plan.stripe_price_id:
        raise StripeAdminActionError(
            f"Plano '{new_plan.display_name}' sem Stripe Price sincronizado."
        )

    try:
        subscription = client.Subscription.retrieve(membership.stripe_subscription_id)
        items_obj = subscription["items"] if "items" in subscription else None
        items = (items_obj["data"] if items_obj is not None and "data" in items_obj else []) or []
        if not items:
            raise StripeAdminActionError(
                "Assinatura sem itens — estado inconsistente."
            )
        first_item_id = items[0]["id"]
        updated = client.Subscription.modify(
            membership.stripe_subscription_id,
            items=[{"id": first_item_id, "price": new_plan.stripe_price_id}],
            proration_behavior="create_prorations",
            metadata={
                "plan_changed_by_admin": str(getattr(admin_user, "pk", "")),
                "plan_id": str(new_plan.pk),
            },
        )
    except StripeAdminActionError:
        raise
    except Exception as exc:
        logger.exception("Falha ao trocar plano da assinatura %s", membership.pk)
        raise StripeAdminActionError(str(exc)) from exc

    membership.plan = new_plan
    membership.save(update_fields=["plan", "updated_at"])
    return membership
