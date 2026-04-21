from django.db import models
from django.conf import settings

from .class_group import ClassGroup
from .common import TimeStampedModel


class WeekdayCode(models.TextChoices):
    MONDAY = "monday", "Segunda-feira"
    TUESDAY = "tuesday", "Terça-feira"
    WEDNESDAY = "wednesday", "Quarta-feira"
    THURSDAY = "thursday", "Quinta-feira"
    FRIDAY = "friday", "Sexta-feira"
    SATURDAY = "saturday", "Sábado"
    SUNDAY = "sunday", "Domingo"


class TrainingStyle(models.TextChoices):
    GI = "gi", "Kimono"
    NO_GI = "no_gi", "Sem kimono"
    MIXED = "mixed", "Misto"


def default_class_schedule_duration_minutes():
    return settings.CLASS_SCHEDULE_DEFAULT_DURATION_MINUTES


class ClassSchedule(TimeStampedModel):
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    weekday = models.CharField(max_length=12, choices=WeekdayCode.choices)
    training_style = models.CharField(
        max_length=12,
        choices=TrainingStyle.choices,
        default=TrainingStyle.MIXED,
    )
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(
        default=default_class_schedule_duration_minutes
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("class_group__display_name", "display_order", "start_time")
        constraints = [
            models.UniqueConstraint(
                fields=("class_group", "weekday", "training_style", "start_time"),
                name="unique_class_schedule_slot",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.class_group.display_name} - "
            f"{self.get_weekday_display()} {self.start_time.strftime('%H:%M')}"
        )
