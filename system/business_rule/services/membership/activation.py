import logging
from django.db import transaction
from django.utils import timezone
from system.business_rule.models.membership import (
    Membership,
    MembershipCreatedVia,
    MembershipStatus,
)
from system.business_rule.services.stripe_notifications import notify_subscription_past_due
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.models.membership_timeline import MembershipTimelineEventType
from system.business_rule.services.membership.cycles import add_billing_cycle, from_unix
from system.business_rule.services.membership.stripe_gateway import extract_stripe_subscription_period, stripe_get

logger = logging.getLogger(__name__)


@transaction.atomic
def activate_membership_from_session(order, stripe_session, stripe_subscription=None):
    person = order.person
    plan = order.plan
    plan_price = order.plan_price_ref
    if plan is None and plan_price is None:
        return None

    subscription_id = ""
    customer_id = ""
    if "subscription" in stripe_session and stripe_session["subscription"]:
        subscription_id = str(stripe_session["subscription"])
    if "customer" in stripe_session and stripe_session["customer"]:
        customer_id = str(stripe_session["customer"])

    current_period_start, current_period_end = extract_stripe_subscription_period(
        stripe_subscription
    )

    defaults = {
        "plan": plan,
        "plan_price": plan_price,
        "status": MembershipStatus.ACTIVE,
        "created_via": MembershipCreatedVia.CHECKOUT,
        "stripe_subscription_id": subscription_id,
        "stripe_customer_id": customer_id or person.stripe_customer_id or "",
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "activated_at": timezone.now(),
    }

    membership = None
    if subscription_id:
        membership = Membership.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()
    if membership is None:
        lookup = {"person": person, "stripe_subscription_id": ""}
        if plan is not None:
            lookup["plan"] = plan
        else:
            lookup["plan_price"] = plan_price
        membership = (
            Membership.objects.filter(**lookup)
            .order_by("-created_at")
            .first()
        )
    if membership is None:
        membership = Membership.objects.create(person=person, **defaults)
    else:
        for field, value in defaults.items():
            setattr(membership, field, value)
        membership.save()


    record_membership_event(
        person,
        MembershipTimelineEventType.PAYMENT_CONFIRMED,
        membership=membership,
        actor=None,
        context={"amount": str(order.total) if order.total is not None else "", "order_id": order.pk},
    )
    return membership


@transaction.atomic
def activate_membership_from_paid_order(
    order,
    *,
    notes="",
    stripe_subscription_id="",
    stripe_subscription_item_id="",
    stripe_customer_id="",
):
    plan = order.plan
    plan_price = order.plan_price_ref
    if plan is None and plan_price is None:
        return None

    now = order.paid_at or timezone.now()
    billing_cycle = plan.billing_cycle if plan is not None else plan_price.billing_cycle
    period_end = add_billing_cycle(now, billing_cycle)
    defaults = {
        "plan": plan,
        "plan_price": plan_price,
        "status": MembershipStatus.ACTIVE,
        "created_via": MembershipCreatedVia.CHECKOUT,
        "current_period_start": now,
        "current_period_end": period_end,
        "activated_at": now,
        "notes": notes or "",
    }
    if stripe_subscription_id:
        defaults["stripe_subscription_id"] = stripe_subscription_id
    if stripe_subscription_item_id:
        defaults["stripe_subscription_item_id"] = stripe_subscription_item_id
    if stripe_customer_id:
        defaults["stripe_customer_id"] = stripe_customer_id

    lookup = {"person": order.person}
    if plan is not None:
        lookup["plan"] = plan
    else:
        lookup["plan_price"] = plan_price
    membership = (
        Membership.objects.filter(**lookup)
        .exclude(status__in=(MembershipStatus.CANCELED, MembershipStatus.EXPIRED))
        .order_by("-created_at")
        .first()
    )
    if membership is None:
        membership = Membership.objects.create(person=order.person, **defaults)
    else:
        for field, value in defaults.items():
            setattr(membership, field, value)
        membership.save()


    record_membership_event(
        order.person,
        MembershipTimelineEventType.PAYMENT_CONFIRMED,
        membership=membership,
        actor=None,
        context={"amount": str(order.total) if order.total is not None else "", "order_id": order.pk},
    )
    return membership


@transaction.atomic
def upsert_membership_from_stripe_subscription(stripe_subscription):
    subscription_id = stripe_subscription["id"]
    memberships = list(
        Membership.objects.filter(stripe_subscription_id=subscription_id)
    )
    if not memberships:
        return None

    status_map = {
        "active": MembershipStatus.ACTIVE,
        "trialing": MembershipStatus.ACTIVE,
        "past_due": MembershipStatus.PAST_DUE,
        "unpaid": MembershipStatus.PAST_DUE,
        "canceled": MembershipStatus.CANCELED,
        "incomplete": MembershipStatus.PENDING,
        "incomplete_expired": MembershipStatus.EXPIRED,
    }
    stripe_status = stripe_get(stripe_subscription, "status", "") or ""
    mapped_status = status_map.get(stripe_status)
    current_period_start, current_period_end = extract_stripe_subscription_period(
        stripe_subscription
    )
    cancel_at_period_end = bool(stripe_get(stripe_subscription, "cancel_at_period_end"))
    canceled_at = stripe_get(stripe_subscription, "canceled_at")
    canceled_at_value = from_unix(canceled_at) if canceled_at else None

    for membership in memberships:
        previous_status = membership.status
        if mapped_status:
            membership.status = mapped_status
        if current_period_start is not None:
            membership.current_period_start = current_period_start
        if current_period_end is not None:
            membership.current_period_end = current_period_end
        membership.cancel_at_period_end = cancel_at_period_end
        if canceled_at_value:
            membership.canceled_at = canceled_at_value
        membership.save()

        if (
            mapped_status == MembershipStatus.PAST_DUE
            and previous_status not in (MembershipStatus.PAST_DUE, MembershipStatus.EXEMPTED)
        ):
            try:
                notify_subscription_past_due(membership)
            except Exception:
                logger.exception(
                    "upsert_membership_from_stripe_subscription: erro ao enviar notificação (membership=%s).",
                    membership.pk,
                )

    return memberships[0]
