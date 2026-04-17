from django.db import models
from django.utils import timezone

from .common import TimeStampedModel


class TrialAccessGrant(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="trial_access_grants",
        verbose_name="Pessoa",
    )
    order = models.OneToOneField(
        "system.RegistrationOrder",
        on_delete=models.CASCADE,
        related_name="trial_access_grant",
        verbose_name="Pedido",
    )
    granted_classes = models.PositiveSmallIntegerField(
        "Aulas concedidas",
        default=1,
    )
    consumed_classes = models.PositiveSmallIntegerField(
        "Aulas consumidas",
        default=0,
    )
    is_active = models.BooleanField("Ativo", default=True)
    activated_at = models.DateTimeField("Ativado em", default=timezone.now)
    consumed_at = models.DateTimeField("Consumido em", null=True, blank=True)
    notes = models.TextField("Observações", blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Concessão de aula experimental"
        verbose_name_plural = "Concessões de aula experimental"

    def __str__(self):
        return f"Trial #{self.pk} — {self.person.full_name}"

    @property
    def remaining_classes(self):
        return max(0, self.granted_classes - self.consumed_classes)

    @property
    def can_consume(self):
        return self.is_active and self.remaining_classes > 0
