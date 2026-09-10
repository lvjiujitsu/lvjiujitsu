from django.db import models


class AuditAction(models.TextChoices):
    CREATED = "created", "Criou"
    UPDATED = "updated", "Alterou"
    DELETED = "deleted", "Excluiu"
    APPROVED = "approved", "Aprovou"
    REFUSED = "refused", "Recusou"


class AuditEntry(models.Model):
    module = models.CharField("módulo", max_length=40)
    action = models.CharField("ação", max_length=30)
    actor_label = models.CharField("autor", max_length=150)
    entity_label = models.CharField("registro", max_length=200)
    summary = models.CharField("resumo", max_length=300, blank=True)
    created_at = models.DateTimeField("registrado em", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"

    def __str__(self):
        return f"{self.action} · {self.entity_label}"
