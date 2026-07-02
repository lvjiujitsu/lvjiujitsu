from django.db import models

from .common import TimeStampedModel


class AuditModule(models.TextChoices):
    PERSON = "person", "Pessoas"
    CHECKIN = "checkin", "Presença"
    FINANCIAL = "financial", "Financeiro"


class AuditAction(models.TextChoices):
    CREATE = "create", "Criação"
    UPDATE = "update", "Atualização"
    DELETE = "delete", "Exclusão"
    APPROVE = "approve", "Aprovação"
    MARK_PAID = "mark_paid", "Marcado como pago"


class OperationalAuditEntry(TimeStampedModel):
    module = models.CharField(max_length=20, choices=AuditModule.choices)
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    actor_label = models.CharField(max_length=150)
    entity_label = models.CharField(max_length=200)
    summary = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Entrada de auditoria operacional"
        verbose_name_plural = "Entradas de auditoria operacional"

    def __str__(self) -> str:
        return f"{self.get_module_display()} · {self.get_action_display()} · {self.entity_label}"
