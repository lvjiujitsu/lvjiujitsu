from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from system.models.base import BaseModel


AUDIENCE_ALL_USERS = "ALL_USERS"
AUDIENCE_ACTIVE_STUDENTS = "ACTIVE_STUDENTS"
AUDIENCE_ACTIVE_HOUSEHOLDS = "ACTIVE_HOUSEHOLDS"
AUDIENCE_INSTRUCTORS = "INSTRUCTORS"
AUDIENCE_STAFF = "STAFF"
AUDIENCE_PENDING_FINANCIAL = "PENDING_FINANCIAL"

COMMUNICATION_AUDIENCE_CHOICES = (
    (AUDIENCE_ALL_USERS, "Todos os usuarios"),
    (AUDIENCE_ACTIVE_STUDENTS, "Alunos ativos com acesso"),
    (AUDIENCE_ACTIVE_HOUSEHOLDS, "Familias ativas"),
    (AUDIENCE_INSTRUCTORS, "Professores"),
    (AUDIENCE_STAFF, "Equipe administrativa"),
    (AUDIENCE_PENDING_FINANCIAL, "Financeiro pendente"),
)


class NoticeBoardMessage(BaseModel):
    title = models.CharField(max_length=255)
    body = models.TextField()
    audience = models.CharField(max_length=32, choices=COMMUNICATION_AUDIENCE_CHOICES, default=AUDIENCE_ALL_USERS)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_notice_board_messages",
    )

    class Meta:
        ordering = ("-starts_at", "-created_at")

    def clean(self):
        super().clean()
        if self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "O fim da vigencia nao pode ser anterior ao inicio."})

    def __str__(self):
        return self.title


class BulkCommunication(BaseModel):
    STATUS_DRAFT = "DRAFT"
    STATUS_QUEUED = "QUEUED"
    STATUS_SENT = "SENT"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_CANCELLED = "CANCELLED"

    CHANNEL_PORTAL = "PORTAL"
    CHANNEL_EMAIL = "EMAIL"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Rascunho"),
        (STATUS_QUEUED, "Na fila"),
        (STATUS_SENT, "Enviado"),
        (STATUS_PARTIAL, "Parcial"),
        (STATUS_CANCELLED, "Cancelado"),
    )
    CHANNEL_CHOICES = (
        (CHANNEL_PORTAL, "Portal"),
        (CHANNEL_EMAIL, "E-mail"),
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    audience = models.CharField(max_length=32, choices=COMMUNICATION_AUDIENCE_CHOICES, default=AUDIENCE_ALL_USERS)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    queued_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivery_stats = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_bulk_communications",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class CommunicationDelivery(BaseModel):
    STATUS_PENDING = "PENDING"
    STATUS_SENT = "SENT"
    STATUS_FAILED = "FAILED"
    STATUS_SKIPPED = "SKIPPED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pendente"),
        (STATUS_SENT, "Enviado"),
        (STATUS_FAILED, "Falhou"),
        (STATUS_SKIPPED, "Ignorado"),
    )

    communication = models.ForeignKey(
        BulkCommunication,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    recipient_user = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.CASCADE,
        related_name="communication_deliveries",
    )
    channel = models.CharField(max_length=16, choices=BulkCommunication.CHANNEL_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("recipient_user__full_name",)
        constraints = [
            models.UniqueConstraint(
                fields=("communication", "recipient_user", "channel"),
                name="uniq_delivery_per_user_channel",
            )
        ]

    def __str__(self):
        return f"{self.communication.title} -> {self.recipient_user.full_name}"
