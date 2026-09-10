from django.db import transaction
from django.utils import timezone
from system.business_rule.models.membership import (
    Membership,
    MembershipCreatedVia,
    MembershipStatus,
)
from system.business_rule.models.registration_order import (
    ApprovalType,
    PaymentProvider,
    PaymentStatus,
)
from system.business_rule.services.financial_transactions import apply_order_financials
from system.business_rule.services.order_stock import apply_order_variant_stock


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
