from celery import shared_task


@shared_task
def dispatch_bulk_communication_task(communication_id):
    from system.services.communications import dispatch_bulk_communication

    dispatch_bulk_communication(communication_id=communication_id)
