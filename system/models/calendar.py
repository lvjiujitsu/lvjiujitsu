from django.db import models
from django.conf import settings
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


class CheckinStatus(models.TextChoices):
    PENDING = "pending", "Aguardando aprovação"
    APPROVED = "approved", "Confirmado"


def default_special_class_title():
    return settings.SPECIAL_CLASS_DEFAULT_TITLE


def default_special_class_duration_minutes():
    return settings.SPECIAL_CLASS_DEFAULT_DURATION_MINUTES


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
    status = models.CharField(
        "Status",
        max_length=16,
        choices=CheckinStatus.choices,
        default=CheckinStatus.PENDING,
    )
    approved_at = models.DateTimeField("Aprovado em", null=True, blank=True)
    approved_by = models.ForeignKey(
        "system.Person",
        on_delete=models.SET_NULL,
        related_name="approved_class_checkins",
        verbose_name="Aprovado por",
        null=True,
        blank=True,
    )

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

    @property
    def is_approved(self):
        return self.status == CheckinStatus.APPROVED


class SpecialClass(TimeStampedModel):
    title = models.CharField(
        "Título",
        max_length=120,
        default=default_special_class_title,
    )
    date = models.DateField("Data")
    start_time = models.TimeField("Horário de início")
    duration_minutes = models.PositiveIntegerField(
        "Duração (min)",
        default=default_special_class_duration_minutes,
    )
    teacher = models.ForeignKey(
        "system.Person",
        on_delete=models.PROTECT,
        related_name="special_classes_taught",
        verbose_name="Professor",
        null=True,
        blank=True,
    )
    notes = models.CharField("Observações", max_length=255, blank=True, default="")

    class Meta:
        ordering = ("date", "start_time")
        verbose_name = "Aulão"
        verbose_name_plural = "Aulões"

    def __str__(self):
        return f"{self.title} — {self.date.strftime('%d/%m/%Y')} {self.start_time.strftime('%H:%M')}"


class SpecialClassCheckin(TimeStampedModel):
    special_class = models.ForeignKey(
        SpecialClass,
        on_delete=models.CASCADE,
        related_name="checkins",
        verbose_name="Aulão",
    )
    person = models.ForeignKey(
        "system.Person",
        on_delete=models.CASCADE,
        related_name="special_class_checkins",
        verbose_name="Pessoa",
    )
    checked_in_at = models.DateTimeField("Check-in em", default=timezone.now)
    status = models.CharField(
        "Status",
        max_length=16,
        choices=CheckinStatus.choices,
        default=CheckinStatus.PENDING,
    )
    approved_at = models.DateTimeField("Aprovado em", null=True, blank=True)
    approved_by = models.ForeignKey(
        "system.Person",
        on_delete=models.SET_NULL,
        related_name="approved_special_class_checkins",
        verbose_name="Aprovado por",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-checked_in_at",)
        verbose_name = "Check-in de aulão"
        verbose_name_plural = "Check-ins de aulão"
        constraints = [
            models.UniqueConstraint(
                fields=("special_class", "person"),
                name="unique_special_class_checkin_per_person",
            ),
        ]

    def __str__(self):
        return f"{self.person.full_name} — {self.special_class}"

    @property
    def is_approved(self):
        return self.status == CheckinStatus.APPROVED
