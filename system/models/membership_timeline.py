from django.db import models

from .common import TimeStampedModel


class MembershipTimelineEventType(models.TextChoices):
    DEPENDENT_ADDED = "dependent_added", "Dependente adicionado"
    DEPENDENT_REMOVED = "dependent_removed", "Dependente removido"
    PAUSE_REQUESTED = "pause_requested", "Pausa solicitada"
    PAUSE_APPROVED = "pause_approved", "Pausa aprovada"
    PAUSE_REJECTED = "pause_rejected", "Pausa recusada"
    PLAN_CHANGED = "plan_changed", "Plano alterado"
    MEMBERSHIP_CANCELED = "membership_canceled", "Assinatura cancelada"
    CARD_UPDATED = "card_updated", "Cartão atualizado"
    PAYMENT_CONFIRMED = "payment_confirmed", "Pagamento confirmado"
    PAYMENT_FAILED = "payment_failed", "Pagamento falhou"
    REFUND_ISSUED = "refund_issued", "Estorno realizado"
    FAMILY_DISCOUNT_CHANGED = "family_discount_changed", "Desconto família alterado"


class MembershipTimelineEvent(TimeStampedModel):
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="timeline_events",
        verbose_name="Pessoa",
    )
    membership = models.ForeignKey(
        "system.Membership",
        on_delete=models.CASCADE,
        related_name="timeline_events",
        verbose_name="Assinatura",
        null=True,
        blank=True,
    )
    event_type = models.CharField(
        "Tipo de evento",
        max_length=32,
        choices=MembershipTimelineEventType.choices,
    )
    actor = models.ForeignKey(
        "system.Person",
        on_delete=models.SET_NULL,
        related_name="timeline_events_caused",
        verbose_name="Realizado por",
        null=True,
        blank=True,
    )
    actor_is_admin = models.BooleanField("Realizado por admin", default=False)
    context = models.JSONField("Contexto", default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Evento de histórico de assinatura"
        verbose_name_plural = "Eventos de histórico de assinatura"
        indexes = [
            models.Index(fields=("person", "-created_at")),
            models.Index(fields=("event_type",)),
        ]

    def __str__(self):
        return f"{self.person.full_name} — {self.get_event_type_display()}"
