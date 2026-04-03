import secrets
from pathlib import Path

from django.db import models
from django.utils import timezone

from system.models.base import BaseModel
from system.models.identity_models import SystemUser
from system.models.student_models import StudentProfile


def consent_term_attachment_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"consent_terms/{instance.code}/v{instance.version}/term{extension or '.pdf'}"


def document_record_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    folder = instance.document_type.lower()
    suffix = extension or ".bin"
    random_token = secrets.token_hex(4)
    return f"documents/{folder}/{timezone.now():%Y/%m/%d}/{random_token}{suffix}"


class ConsentTerm(BaseModel):
    AUDIENCE_ALL = "all"
    AUDIENCE_GUARDIAN = "guardian"
    AUDIENCE_STUDENT = "student"

    AUDIENCE_CHOICES = (
        (AUDIENCE_ALL, "Todos"),
        (AUDIENCE_GUARDIAN, "Responsavel"),
        (AUDIENCE_STUDENT, "Aluno"),
    )

    code = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    audience = models.CharField(max_length=24, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL)
    content = models.TextField()
    attachment = models.FileField(upload_to=consent_term_attachment_upload_to, blank=True)
    is_active = models.BooleanField(default=True)
    required_for_onboarding = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("code", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("code", "version"),
                name="uniq_consent_term_version",
            )
        ]

    def __str__(self):
        return f"{self.title} v{self.version}"


class ConsentAcceptance(BaseModel):
    CONTEXT_ONBOARDING = "onboarding"
    CONTEXT_PROFILE = "profile"

    CONTEXT_CHOICES = (
        (CONTEXT_ONBOARDING, "Onboarding"),
        (CONTEXT_PROFILE, "Perfil"),
    )

    user = models.ForeignKey(
        SystemUser,
        on_delete=models.CASCADE,
        related_name="consent_acceptances",
    )
    term = models.ForeignKey(
        ConsentTerm,
        on_delete=models.CASCADE,
        related_name="acceptances",
    )
    accepted_at = models.DateTimeField(default=timezone.now)
    context = models.CharField(max_length=32, choices=CONTEXT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-accepted_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "term"),
                name="uniq_user_term_acceptance",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} aceitou {self.term}"


class DocumentRecord(BaseModel):
    TYPE_CONTRACT = "CONTRACT"
    TYPE_AUTHORIZATION = "AUTHORIZATION"
    TYPE_MEDICAL = "MEDICAL"
    TYPE_OTHER = "OTHER"

    TYPE_CHOICES = (
        (TYPE_CONTRACT, "Contrato"),
        (TYPE_AUTHORIZATION, "Autorizacao"),
        (TYPE_MEDICAL, "Documento medico"),
        (TYPE_OTHER, "Outro"),
    )

    owner_user = models.ForeignKey(
        SystemUser,
        on_delete=models.CASCADE,
        related_name="document_records",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="document_records",
    )
    subscription = models.ForeignKey(
        "system.LocalSubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_records",
    )
    uploaded_by = models.ForeignKey(
        SystemUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_document_records",
    )
    document_type = models.CharField(max_length=24, choices=TYPE_CHOICES, default=TYPE_OTHER)
    title = models.CharField(max_length=255)
    version_label = models.CharField(max_length=64, blank=True)
    file = models.FileField(upload_to=document_record_upload_to)
    original_filename = models.CharField(max_length=255)
    issued_at = models.DateTimeField(default=timezone.now)
    is_visible_to_owner = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-issued_at", "-created_at")

    def __str__(self):
        return f"{self.title} - {self.owner_user.full_name}"


class LgpdRequest(BaseModel):
    TYPE_ACCESS = "ACCESS"
    TYPE_CORRECTION = "CORRECTION"
    TYPE_ANONYMIZATION = "ANONYMIZATION"
    TYPE_DELETION = "DELETION"

    STATUS_OPEN = "OPEN"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_REJECTED = "REJECTED"

    TYPE_CHOICES = (
        (TYPE_ACCESS, "Acesso"),
        (TYPE_CORRECTION, "Correcao"),
        (TYPE_ANONYMIZATION, "Anonimizacao"),
        (TYPE_DELETION, "Eliminacao"),
    )
    STATUS_CHOICES = (
        (STATUS_OPEN, "Aberto"),
        (STATUS_IN_PROGRESS, "Em andamento"),
        (STATUS_COMPLETED, "Concluido"),
        (STATUS_REJECTED, "Recusado"),
    )

    user = models.ForeignKey(
        SystemUser,
        on_delete=models.CASCADE,
        related_name="lgpd_requests",
    )
    request_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_OPEN)
    notes = models.TextField(blank=True)
    confirmation_code = models.CharField(max_length=48, unique=True, null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        SystemUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_lgpd_requests",
    )
    processing_notes = models.TextField(blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def requires_confirmation(self):
        return self.request_type in {self.TYPE_ANONYMIZATION, self.TYPE_DELETION}

    @property
    def is_confirmed(self):
        return self.confirmed_at is not None

    def __str__(self):
        return f"{self.user.full_name} - {self.request_type}"


class SensitiveAccessLog(BaseModel):
    ACCESS_EMERGENCY_VIEW = "emergency_view"
    ACCESS_EMERGENCY_UPDATE = "emergency_update"
    ACCESS_CONSENT_VIEW = "consent_view"

    ACCESS_CHOICES = (
        (ACCESS_EMERGENCY_VIEW, "Consulta de prontuario"),
        (ACCESS_EMERGENCY_UPDATE, "Atualizacao de prontuario"),
        (ACCESS_CONSENT_VIEW, "Consulta de consentimentos"),
    )

    actor_user = models.ForeignKey(
        SystemUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sensitive_access_logs",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="sensitive_access_logs",
    )
    access_type = models.CharField(max_length=32, choices=ACCESS_CHOICES)
    access_purpose = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.access_type} - {self.student.user.full_name}"
