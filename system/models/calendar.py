from django.db import models
from django.utils import timezone

from .common import TimeStampedModel


class Holiday(TimeStampedModel):
    date = models.DateField("Data", unique=True)
    name = models.CharField("Nome", max_length=200)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ("date",)
        verbose_name = "Feriado"
        verbose_name_plural = "Feriados"

    def __str__(self):
        return f"{self.date.strftime('%d/%m/%Y')} — {self.name}"


class SessionStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Agendada"
    CANCELLED = "cancelled", "Cancelada"


class ClassSession(TimeStampedModel):
    schedule = models.ForeignKey(
        "system.ClassSchedule",
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Horário",
    )
    date = models.DateField("Data")
    status = models.CharField(
        "Status",
        max_length=16,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
    )
    cancellation_reason = models.CharField(
        "Motivo do cancelamento",
        max_length=255,
        blank=True,
        default="",
    )

    class Meta:
        ordering = ("date", "schedule__start_time")
        verbose_name = "Sessão de aula"
        verbose_name_plural = "Sessões de aula"
        constraints = [
            models.UniqueConstraint(
                fields=("schedule", "date"),
                name="unique_class_session_per_day",
            ),
        ]

    def __str__(self):
        return f"{self.schedule} — {self.date.strftime('%d/%m/%Y')}"

    @property
    def is_cancelled(self):
        return self.status == SessionStatus.CANCELLED


class ClassCheckin(TimeStampedModel):
    session = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE,
        related_name="checkins",
        verbose_name="Sessão",
    )
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="class_checkins",
        verbose_name="Pessoa",
    )
    checked_in_at = models.DateTimeField("Check-in em", default=timezone.now)

    class Meta:
        ordering = ("-checked_in_at",)
        verbose_name = "Check-in"
        verbose_name_plural = "Check-ins"
        constraints = [
            models.UniqueConstraint(
                fields=("session", "person"),
                name="unique_checkin_per_session",
            ),
        ]

    def __str__(self):
        return f"{self.person.full_name} — {self.session}"
