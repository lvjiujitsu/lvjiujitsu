from django.conf import settings
from django.db import models

from system.models.base import BaseModel


class AuditLog(BaseModel):
    CATEGORY_AUTH = "AUTH"
    CATEGORY_FINANCE = "FINANCE"
    CATEGORY_PAYMENTS = "PAYMENTS"
    CATEGORY_ATTENDANCE = "ATTENDANCE"
    CATEGORY_GRADUATION = "GRADUATION"
    CATEGORY_DOCUMENTS = "DOCUMENTS"
    CATEGORY_EMERGENCY = "EMERGENCY"
    CATEGORY_PDV = "PDV"
    CATEGORY_REPORTS = "REPORTS"
    CATEGORY_SYSTEM = "SYSTEM"

    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILURE = "FAILURE"

    CATEGORY_CHOICES = (
        (CATEGORY_AUTH, "Autenticacao"),
        (CATEGORY_FINANCE, "Financeiro"),
        (CATEGORY_PAYMENTS, "Pagamentos"),
        (CATEGORY_ATTENDANCE, "Presenca"),
        (CATEGORY_GRADUATION, "Graduacao"),
        (CATEGORY_DOCUMENTS, "Documentos"),
        (CATEGORY_EMERGENCY, "Emergencia"),
        (CATEGORY_PDV, "PDV"),
        (CATEGORY_REPORTS, "Relatorios"),
        (CATEGORY_SYSTEM, "Sistema"),
    )
    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Sucesso"),
        (STATUS_FAILURE, "Falha"),
    )

    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    action = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    target_model = models.CharField(max_length=64, blank=True)
    target_uuid = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.category}:{self.action}:{self.status}"


class CsvExportControl(BaseModel):
    STATUS_VALID = "VALID"
    STATUS_INVALID = "INVALID"
    STATUS_ERROR = "ERROR"

    STATUS_CHOICES = (
        (STATUS_VALID, "Valido"),
        (STATUS_INVALID, "Invalido"),
        (STATUS_ERROR, "Erro"),
    )

    name = models.CharField(max_length=64, unique=True)
    control_file_path = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    last_validation_status = models.CharField(max_length=16, choices=STATUS_CHOICES, blank=True)
    last_validation_message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ExportRequest(BaseModel):
    TYPE_ATTENDANCE = "ATTENDANCE"
    TYPE_FINANCE = "FINANCE"
    TYPE_GRADUATION = "GRADUATION"
    TYPE_AUDIT = "AUDIT"

    STATUS_PENDING = "PENDING"
    STATUS_SUCCEEDED = "SUCCEEDED"
    STATUS_FAILED = "FAILED"

    TYPE_CHOICES = (
        (TYPE_ATTENDANCE, "Presenca"),
        (TYPE_FINANCE, "Financeiro"),
        (TYPE_GRADUATION, "Graduacao"),
        (TYPE_AUDIT, "Auditoria"),
    )
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pendente"),
        (STATUS_SUCCEEDED, "Concluido"),
        (STATUS_FAILED, "Falhou"),
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="export_requests",
    )
    report_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    filters = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=255, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    error_message = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-started_at", "-created_at")

    def __str__(self):
        return f"{self.report_type}:{self.status}"
