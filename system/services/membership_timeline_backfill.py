from system.models.membership import (
    Membership,
    MembershipPauseRequest,
    MembershipPauseRequestStatus,
)
from system.models.membership_timeline import (
    MembershipTimelineEvent,
    MembershipTimelineEventType,
)
from system.models.registration_order import RegistrationOrder
from system.services.membership_timeline import record_membership_event


def _record_backfilled_event(person, event_type, *, source_id, created_at, **kwargs):
    if MembershipTimelineEvent.objects.filter(context__source_id=source_id).exists():
        return False
    context = kwargs.pop("context", {}) or {}
    context.update({"backfilled": True, "source_id": source_id})
    event = record_membership_event(person, event_type, context=context, **kwargs)
    MembershipTimelineEvent.objects.filter(pk=event.pk).update(created_at=created_at)
    return True


def backfill_membership_cancellations():
    created = 0
    for membership in (
        Membership.objects.filter(canceled_at__isnull=False).select_related("person")
    ):
        added = _record_backfilled_event(
            membership.person,
            MembershipTimelineEventType.MEMBERSHIP_CANCELED,
            source_id=f"membership_canceled:{membership.pk}",
            created_at=membership.canceled_at,
            membership=membership,
            context={"plan_name": membership.effective_display_name},
        )
        created += int(added)
    return created


def backfill_order_payments():
    created = 0
    for order in (
        RegistrationOrder.objects.filter(paid_at__isnull=False).select_related("person")
    ):
        added = _record_backfilled_event(
            order.person,
            MembershipTimelineEventType.PAYMENT_CONFIRMED,
            source_id=f"order_paid:{order.pk}",
            created_at=order.paid_at,
            context={"amount": str(order.total) if order.total is not None else "", "order_id": order.pk},
        )
        created += int(added)
    return created


def backfill_order_refunds():
    created = 0
    for order in (
        RegistrationOrder.objects.filter(refunded_at__isnull=False).select_related("person")
    ):
        added = _record_backfilled_event(
            order.person,
            MembershipTimelineEventType.REFUND_ISSUED,
            source_id=f"order_refunded:{order.pk}",
            created_at=order.refunded_at,
            context={"amount": str(order.total) if order.total is not None else "", "order_id": order.pk},
        )
        created += int(added)
    return created


def backfill_pause_requests():
    created = 0
    for pause in (
        MembershipPauseRequest.objects.select_related("membership__person")
    ):
        person = pause.membership.person
        created += int(_record_backfilled_event(
            person,
            MembershipTimelineEventType.PAUSE_REQUESTED,
            source_id=f"pause_requested:{pause.pk}",
            created_at=pause.created_at,
            membership=pause.membership,
            context={
                "kind": pause.kind,
                "start_date": pause.requested_start_date.isoformat(),
                "end_date": pause.requested_end_date.isoformat(),
            },
        ))
        if pause.status == MembershipPauseRequestStatus.APPROVED and pause.decided_at:
            created += int(_record_backfilled_event(
                person,
                MembershipTimelineEventType.PAUSE_APPROVED,
                source_id=f"pause_approved:{pause.pk}",
                created_at=pause.decided_at,
                membership=pause.membership,
                actor_is_admin=True,
                context={"kind": pause.kind, "duration_days": pause.duration_days},
            ))
        elif pause.status == MembershipPauseRequestStatus.REJECTED and pause.decided_at:
            created += int(_record_backfilled_event(
                person,
                MembershipTimelineEventType.PAUSE_REJECTED,
                source_id=f"pause_rejected:{pause.pk}",
                created_at=pause.decided_at,
                membership=pause.membership,
                actor_is_admin=True,
                context={"kind": pause.kind, "decision_notes": pause.decision_notes},
            ))
    return created


def backfill_membership_timeline():
    return {
        "cancellations": backfill_membership_cancellations(),
        "payments": backfill_order_payments(),
        "refunds": backfill_order_refunds(),
        "pauses": backfill_pause_requests(),
    }
