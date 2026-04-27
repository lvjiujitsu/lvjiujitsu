import calendar
import logging
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from system.models.membership import (
    Membership,
    MembershipCreatedVia,
    MembershipInvoice,
    MembershipStatus,
)
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.models.plan import BillingCycle
from system.models.plan import SubscriptionPlan
from system.models.registration_order import (
    ApprovalType,
    PaymentProvider,
    PaymentStatus,
    RegistrationOrder,
)
from system.services.financial_transactions import apply_order_financials
from system.runtime_config import payment_currency


logger = logging.getLogger(__name__)


def _sget(obj, key, default=None):
    """Leitura segura em StripeObject (não suporta .get())."""
    if obj is None:
        return default
    try:
        if key in obj:
            value = obj[key]
            return value if value is not None else default
    except (TypeError, KeyError):
        return default
    return default


def _from_unix(value):
    if value in (None, 0):
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=dt_timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


MONTHS_BY_BILLING_CYCLE = {
    BillingCycle.MONTHLY: 1,
    BillingCycle.QUARTERLY: 3,
    BillingCycle.SEMIANNUAL: 6,
    BillingCycle.ANNUAL: 12,
}


def add_billing_cycle(start, billing_cycle):
    months = MONTHS_BY_BILLING_CYCLE.get(billing_cycle, 1)
    return _add_months(start, months)


def get_billing_cycle_day_count(start, billing_cycle):
    end = add_billing_cycle(start, billing_cycle)
    return max((end - start).days, 1)


def _add_months(value, months):
    month_index = value.month - 1 + months
    target_year = value.year + month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(value.day, calendar.monthrange(target_year, target_month)[1])
    return value.replace(year=target_year, month=target_month, day=target_day)


@transaction.atomic
def activate_membership_from_session(order, stripe_session, stripe_subscription=None):
    person = order.person
    plan = order.plan
    if plan is None:
        return None

    subscription_id = ""
    customer_id = ""
    if "subscription" in stripe_session and stripe_session["subscription"]:
        subscription_id = str(stripe_session["subscription"])
    if "customer" in stripe_session and stripe_session["customer"]:
        customer_id = str(stripe_session["customer"])

    current_period_start = None
    current_period_end = None
    if stripe_subscription is not None:
        current_period_start = _from_unix(
            _sget(stripe_subscription, "current_period_start")
        )
        current_period_end = _from_unix(
            _sget(stripe_subscription, "current_period_end")
        )

    defaults = {
        "plan": plan,
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
        membership = (
            Membership.objects.filter(
                person=person,
                plan=plan,
                stripe_subscription_id="",
            )
            .order_by("-created_at")
            .first()
        )
    if membership is None:
        membership = Membership.objects.create(person=person, **defaults)
    else:
        for field, value in defaults.items():
            setattr(membership, field, value)
        membership.save()
    return membership


@transaction.atomic
def activate_membership_from_paid_order(order, *, notes=""):
    plan = order.plan
    if plan is None:
        return None

    now = order.paid_at or timezone.now()
    period_end = add_billing_cycle(now, plan.billing_cycle)
    defaults = {
        "plan": plan,
        "status": MembershipStatus.ACTIVE,
        "created_via": MembershipCreatedVia.CHECKOUT,
        "current_period_start": now,
        "current_period_end": period_end,
        "activated_at": now,
        "notes": notes or "",
    }

    membership = (
        Membership.objects.filter(
            person=order.person,
            plan=plan,
        )
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
    return membership


@transaction.atomic
def upsert_membership_from_stripe_subscription(stripe_subscription):
    subscription_id = stripe_subscription["id"]
    membership = Membership.objects.filter(
        stripe_subscription_id=subscription_id
    ).first()
    if membership is None:
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
    stripe_status = _sget(stripe_subscription, "status", "") or ""
    mapped_status = status_map.get(stripe_status)
    if mapped_status:
        membership.status = mapped_status

    membership.current_period_start = _from_unix(
        _sget(stripe_subscription, "current_period_start")
    )
    membership.current_period_end = _from_unix(
        _sget(stripe_subscription, "current_period_end")
    )
    membership.cancel_at_period_end = bool(
        _sget(stripe_subscription, "cancel_at_period_end")
    )
    canceled_at = _sget(stripe_subscription, "canceled_at")
    if canceled_at:
        membership.canceled_at = _from_unix(canceled_at)
    membership.save()
    return membership


@transaction.atomic
def record_invoice_from_stripe(stripe_invoice):
    subscription_id = _sget(stripe_invoice, "subscription")
    if not subscription_id:
        return None
    membership = Membership.objects.filter(
        stripe_subscription_id=str(subscription_id)
    ).first()
    if membership is None:
        return None

    invoice_id = stripe_invoice["id"]
    amount_paid = Decimal(_sget(stripe_invoice, "amount_paid", 0) or 0) / Decimal("100")
    lines = _sget(stripe_invoice, "lines")
    period_start = None
    period_end = None
    line_data = _sget(lines, "data") if lines is not None else None
    if line_data:
        first_line = line_data[0]
        period = _sget(first_line, "period")
        if period is not None:
            period_start = _from_unix(_sget(period, "start"))
            period_end = _from_unix(_sget(period, "end"))

    status_transitions = _sget(stripe_invoice, "status_transitions")
    paid_at_unix = _sget(status_transitions, "paid_at") if status_transitions is not None else None

    defaults = {
        "membership": membership,
        "amount_paid": amount_paid,
        "currency": _sget(stripe_invoice, "currency", payment_currency()) or payment_currency(),
        "status": _sget(stripe_invoice, "status", "paid") or "paid",
        "period_start": period_start,
        "period_end": period_end,
        "hosted_invoice_url": _sget(stripe_invoice, "hosted_invoice_url", "") or "",
        "stripe_payment_intent_id": str(_sget(stripe_invoice, "payment_intent", "") or ""),
        "paid_at": _from_unix(paid_at_unix) or timezone.now(),
        "description": (_sget(stripe_invoice, "description", "") or "")[:255],
    }

    invoice, _ = MembershipInvoice.objects.update_or_create(
        stripe_invoice_id=invoice_id,
        defaults=defaults,
    )
    if period_end:
        membership.current_period_end = period_end
    if period_start:
        membership.current_period_start = period_start
    if membership.status in (MembershipStatus.PENDING, MembershipStatus.PAST_DUE):
        membership.status = MembershipStatus.ACTIVE
    membership.last_invoice_id = invoice_id
    membership.save(
        update_fields=[
            "current_period_start",
            "current_period_end",
            "status",
            "last_invoice_id",
            "updated_at",
        ]
    )
    return invoice


@transaction.atomic
def mark_invoice_failed(stripe_invoice):
    subscription_id = _sget(stripe_invoice, "subscription")
    if not subscription_id:
        return None
    membership = Membership.objects.filter(
        stripe_subscription_id=str(subscription_id)
    ).first()
    if membership is None:
        return None
    if membership.status == MembershipStatus.EXEMPTED:
        return membership
    membership.status = MembershipStatus.PAST_DUE
    membership.save(update_fields=["status", "updated_at"])
    return membership


@transaction.atomic
def mark_membership_canceled(stripe_subscription):
    membership = Membership.objects.filter(
        stripe_subscription_id=stripe_subscription["id"]
    ).first()
    if membership is None:
        return None
    membership.status = MembershipStatus.CANCELED
    membership.cancel_at_period_end = False
    membership.canceled_at = _from_unix(_sget(stripe_subscription, "canceled_at")) or timezone.now()
    membership.save(
        update_fields=["status", "cancel_at_period_end", "canceled_at", "updated_at"]
    )
    return membership


@transaction.atomic
def record_refund_from_charge(stripe_charge):
    payment_intent_id = _sget(stripe_charge, "payment_intent")
    amount_refunded = Decimal(_sget(stripe_charge, "amount_refunded", 0) or 0) / Decimal("100")

    order = None
    if payment_intent_id:
        order = RegistrationOrder.objects.filter(
            stripe_payment_intent_id=str(payment_intent_id)
        ).first()
    if order is not None:
        order.refunded_at = timezone.now()
        if amount_refunded >= (order.total or Decimal("0")):
            order.payment_status = PaymentStatus.REFUNDED
        order.save(update_fields=["refunded_at", "payment_status", "updated_at"])

    invoice = None
    if payment_intent_id:
        invoice = MembershipInvoice.objects.filter(
            stripe_payment_intent_id=str(payment_intent_id)
        ).first()
    if invoice is not None:
        invoice.amount_refunded = amount_refunded
        invoice.refunded_at = timezone.now()
        invoice.save(update_fields=["amount_refunded", "refunded_at", "updated_at"])

    return {"order": order, "invoice": invoice}


@transaction.atomic
def exempt_order(order, admin_user, notes=""):
    order.payment_status = PaymentStatus.EXEMPTED
    order.approval_type = ApprovalType.EXEMPT
    order.approved_by = admin_user
    order.approved_at = timezone.now()
    order.approval_notes = notes or ""
    order.save(
        update_fields=[
            "payment_status",
            "approval_type",
            "approved_by",
            "approved_at",
            "approval_notes",
            "updated_at",
        ]
    )
    from system.services.registration_checkout import apply_order_variant_stock

    apply_order_variant_stock(order)
    if order.plan_id:
        _ensure_exempted_membership(order, admin_user, notes)
    return order


@transaction.atomic
def mark_order_manually_paid(order, admin_user, notes=""):
    was_paid = order.payment_status in (PaymentStatus.PAID, PaymentStatus.EXEMPTED)
    order.payment_status = PaymentStatus.PAID
    order.paid_at = timezone.now()
    order.approval_type = ApprovalType.MANUAL_PAID
    order.approved_by = admin_user
    order.approved_at = timezone.now()
    order.approval_notes = notes or ""
    order.save(
        update_fields=[
            "payment_status",
            "paid_at",
            "approval_type",
            "approved_by",
            "approved_at",
            "approval_notes",
            "updated_at",
        ]
    )
    from system.services.registration_checkout import apply_order_variant_stock

    if not was_paid:
        apply_order_variant_stock(order)
    if order.plan_id:
        _ensure_manual_paid_membership(order, admin_user, notes)
    apply_order_financials(
        order,
        payment_provider=order.payment_provider or PaymentProvider.MANUAL,
        mark_available=True,
    )
    return order


def _ensure_exempted_membership(order, admin_user, notes):
    membership, created = Membership.objects.get_or_create(
        person=order.person,
        plan=order.plan,
        status__in=(MembershipStatus.PENDING, MembershipStatus.EXEMPTED),
        defaults={
            "status": MembershipStatus.EXEMPTED,
            "created_via": MembershipCreatedVia.EXEMPTION,
            "activated_at": timezone.now(),
            "notes": notes or "",
        },
    )
    if not created:
        membership.status = MembershipStatus.EXEMPTED
        membership.created_via = MembershipCreatedVia.EXEMPTION
        membership.activated_at = membership.activated_at or timezone.now()
        membership.notes = notes or membership.notes
        membership.save()
    return membership


def _ensure_manual_paid_membership(order, admin_user, notes):
    plan = order.plan
    membership, created = Membership.objects.get_or_create(
        person=order.person,
        plan=plan,
        status=MembershipStatus.PENDING,
        defaults={
            "status": MembershipStatus.ACTIVE,
            "created_via": MembershipCreatedVia.MANUAL_PAID,
            "activated_at": timezone.now(),
            "notes": notes or "",
        },
    )
    if not created:
        membership.status = MembershipStatus.ACTIVE
        membership.created_via = MembershipCreatedVia.MANUAL_PAID
        membership.activated_at = membership.activated_at or timezone.now()
        membership.notes = notes or membership.notes
        membership.save()
    return membership


def get_active_membership(person):
    billing_person = get_membership_owner(person)
    return _ensure_active_membership_for_person(billing_person)


def get_membership_owner(person):
    if person is None:
        return None
    if _person_has_financial_records(person):
        return person
    for responsible in _get_responsible_people(person):
        if _person_has_financial_records(responsible):
            return responsible
    return person


def _get_responsible_people(person):
    relationships = (
        PersonRelationship.objects.filter(
            target_person=person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            source_person__is_active=True,
        )
        .select_related("source_person")
        .order_by("-created_at")
    )
    return [item.source_person for item in relationships]


def _person_has_financial_records(person):
    return Membership.objects.filter(person=person).exists() or RegistrationOrder.objects.filter(
        person=person
    ).exists()


def _ensure_active_membership_for_person(person):
    if person is None:
        return None
    active_membership = (
        Membership.objects.filter(person=person)
        .exclude(status__in=(MembershipStatus.EXPIRED, MembershipStatus.CANCELED))
        .order_by("-created_at")
        .first()
    )
    if active_membership is not None:
        return active_membership
    latest_paid_order = (
        RegistrationOrder.objects.filter(
            person=person,
            plan__isnull=False,
            payment_status__in=(PaymentStatus.PAID, PaymentStatus.EXEMPTED),
        )
        .exclude(total__lte=Decimal("0"))
        .order_by("-paid_at", "-created_at")
        .first()
    )
    if latest_paid_order is None:
        return None
    return activate_membership_from_paid_order(
        latest_paid_order,
        notes="Assinatura sincronizada a partir de pedido já pago.",
    )


def get_guardian_billing_tabs(guardian_person):
    dependents_qs = (
        PersonRelationship.objects.filter(
            source_person=guardian_person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        .select_related("target_person")
        .order_by("target_person__full_name")
    )
    tabs = [_build_billing_tab(guardian_person, is_active=True)]
    for rel in dependents_qs:
        tabs.append(_build_billing_tab(rel.target_person, is_active=False))
    return tabs


def _build_billing_tab(person, *, is_active=False):
    active_membership = get_active_membership(person)
    pending_order = get_latest_open_order(person)
    recent_invoices = []
    if active_membership is not None:
        recent_invoices = list(
            MembershipInvoice.objects.filter(membership=active_membership)
            .order_by("-paid_at", "-created_at")[:5]
        )
    return {
        "person": person,
        "active_membership": active_membership,
        "pending_order": pending_order,
        "recent_invoices": recent_invoices,
        "is_active_tab": is_active,
    }


def has_dependents(person):
    return PersonRelationship.objects.filter(
        source_person=person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    ).exists()


def get_latest_open_order(person):
    billing_person = get_membership_owner(person)
    if billing_person is None:
        return None
    return (
        RegistrationOrder.objects.filter(person=billing_person, total__gt=0)
        .exclude(
            payment_status__in=(
                PaymentStatus.PAID,
                PaymentStatus.EXEMPTED,
                PaymentStatus.REFUNDED,
            )
        )
        .order_by("-created_at")
        .first()
    )
