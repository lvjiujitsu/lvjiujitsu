import factory
from django.utils import timezone

from system.models import (
    AUDIENCE_ALL_USERS,
    BulkCommunication,
    CommunicationDelivery,
    NoticeBoardMessage,
)
from system.tests.factories.auth_factories import SystemUserFactory


class NoticeBoardMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NoticeBoardMessage

    title = factory.Sequence(lambda index: f"Aviso {index}")
    body = "Mensagem do mural"
    audience = AUDIENCE_ALL_USERS
    starts_at = factory.LazyFunction(timezone.now)
    is_active = True
    created_by = factory.SubFactory(SystemUserFactory)


class BulkCommunicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BulkCommunication

    title = factory.Sequence(lambda index: f"Comunicado {index}")
    message = "Mensagem institucional"
    audience = AUDIENCE_ALL_USERS
    channel = BulkCommunication.CHANNEL_PORTAL
    status = BulkCommunication.STATUS_QUEUED
    queued_at = factory.LazyFunction(timezone.now)
    created_by = factory.SubFactory(SystemUserFactory)


class CommunicationDeliveryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommunicationDelivery

    communication = factory.SubFactory(BulkCommunicationFactory)
    recipient_user = factory.SubFactory(SystemUserFactory)
    channel = BulkCommunication.CHANNEL_PORTAL
    status = CommunicationDelivery.STATUS_PENDING
