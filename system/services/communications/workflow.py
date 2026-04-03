from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from system.models import BulkCommunication, CommunicationDelivery, NoticeBoardMessage
from system.selectors.communication_selectors import get_recipient_users_for_audience


@transaction.atomic
def create_notice_board_message(*, actor_user, title, body, audience, starts_at, ends_at=None, is_active=True):
    notice = NoticeBoardMessage(
        title=title,
        body=body,
        audience=audience,
        starts_at=starts_at,
        ends_at=ends_at,
        is_active=is_active,
        created_by=actor_user,
    )
    notice.full_clean()
    notice.save()
    return notice


@transaction.atomic
def create_bulk_communication(*, actor_user, title, message, audience, channel):
    communication = BulkCommunication(
        title=title,
        message=message,
        audience=audience,
        channel=channel,
        status=BulkCommunication.STATUS_QUEUED,
        queued_at=timezone.now(),
        created_by=actor_user,
    )
    communication.full_clean()
    communication.save()
    _create_deliveries(communication)
    if settings.CELERY_TASK_ALWAYS_EAGER:
        _dispatch_after_commit(communication.id)
        return communication
    transaction.on_commit(lambda: _dispatch_after_commit(communication.id))
    return communication


@transaction.atomic
def dispatch_bulk_communication(*, communication_id):
    communication = BulkCommunication.objects.select_for_update().get(id=communication_id)
    deliveries = communication.deliveries.select_related("recipient_user").filter(status=CommunicationDelivery.STATUS_PENDING)
    if not deliveries.exists():
        return _finalize_communication(communication)
    for delivery in deliveries:
        _dispatch_delivery(communication, delivery)
    return _finalize_communication(communication)


def _create_deliveries(communication):
    recipients = get_recipient_users_for_audience(communication.audience)
    deliveries = []
    for recipient in recipients:
        deliveries.append(
            CommunicationDelivery(
                communication=communication,
                recipient_user=recipient,
                channel=communication.channel,
            )
        )
    CommunicationDelivery.objects.bulk_create(deliveries, ignore_conflicts=True)


def _dispatch_after_commit(communication_id):
    from system.tasks import dispatch_bulk_communication_task

    dispatch_bulk_communication_task.delay(communication_id)


def _dispatch_delivery(communication, delivery):
    if communication.channel == BulkCommunication.CHANNEL_PORTAL:
        return _mark_delivery_sent(delivery, metadata={"channel": "portal"})
    return _dispatch_email_delivery(communication, delivery)


def _dispatch_email_delivery(communication, delivery):
    recipient = delivery.recipient_user
    if not recipient.email:
        return _mark_delivery_failed(delivery, "Usuario sem e-mail cadastrado.")
    send_mail(
        subject=communication.title,
        message=communication.message,
        from_email=None,
        recipient_list=[recipient.email],
        fail_silently=False,
    )
    return _mark_delivery_sent(delivery, metadata={"channel": "email", "email": recipient.email})


def _mark_delivery_sent(delivery, *, metadata):
    delivery.status = CommunicationDelivery.STATUS_SENT
    delivery.delivered_at = timezone.now()
    delivery.metadata = metadata
    delivery.save(update_fields=["status", "delivered_at", "metadata", "updated_at"])
    return delivery


def _mark_delivery_failed(delivery, reason):
    delivery.status = CommunicationDelivery.STATUS_FAILED
    delivery.failure_reason = reason
    delivery.save(update_fields=["status", "failure_reason", "updated_at"])
    return delivery


def _finalize_communication(communication):
    stats = _build_delivery_stats(communication)
    communication.delivery_stats = stats
    communication.dispatched_at = timezone.now()
    communication.status = _resolve_communication_status(stats)
    communication.save(update_fields=["delivery_stats", "dispatched_at", "status", "updated_at"])
    return communication


def _build_delivery_stats(communication):
    deliveries = communication.deliveries.values("status")
    sent = 0
    failed = 0
    skipped = 0
    for row in deliveries:
        if row["status"] == CommunicationDelivery.STATUS_SENT:
            sent += 1
        if row["status"] == CommunicationDelivery.STATUS_FAILED:
            failed += 1
        if row["status"] == CommunicationDelivery.STATUS_SKIPPED:
            skipped += 1
    return {"sent": sent, "failed": failed, "skipped": skipped, "total": sent + failed + skipped}


def _resolve_communication_status(stats):
    if stats["failed"] and stats["sent"]:
        return BulkCommunication.STATUS_PARTIAL
    if stats["failed"] and not stats["sent"]:
        return BulkCommunication.STATUS_PARTIAL
    return BulkCommunication.STATUS_SENT
