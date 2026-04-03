from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from system.models.base import BaseModel


class IbjjfBelt(BaseModel):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    display_order = models.PositiveIntegerField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order",)

    def __str__(self):
        return self.name


class ClassDiscipline(BaseModel):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ClassGroup(BaseModel):
    WEEKDAY_MONDAY = 0
    WEEKDAY_TUESDAY = 1
    WEEKDAY_WEDNESDAY = 2
    WEEKDAY_THURSDAY = 3
    WEEKDAY_FRIDAY = 4
    WEEKDAY_SATURDAY = 5
    WEEKDAY_SUNDAY = 6

    WEEKDAY_CHOICES = (
        (WEEKDAY_MONDAY, "Segunda"),
        (WEEKDAY_TUESDAY, "Terca"),
        (WEEKDAY_WEDNESDAY, "Quarta"),
        (WEEKDAY_THURSDAY, "Quinta"),
        (WEEKDAY_FRIDAY, "Sexta"),
        (WEEKDAY_SATURDAY, "Sabado"),
        (WEEKDAY_SUNDAY, "Domingo"),
    )

    name = models.CharField(max_length=128)
    modality = models.ForeignKey(
        ClassDiscipline,
        on_delete=models.PROTECT,
        related_name="class_groups",
    )
    instructor = models.ForeignKey(
        "system.InstructorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_groups",
    )
    reference_belt = models.ForeignKey(
        IbjjfBelt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_groups",
    )
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=1)
    reservation_required = models.BooleanField(default=False)
    minimum_age = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("weekday", "start_time", "name")

    def clean(self):
        super().clean()
        self._validate_schedule()
        self._validate_capacity()

    def _validate_schedule(self):
        if self.end_time <= self.start_time:
            raise ValidationError({"end_time": "Horario final deve ser posterior ao inicial."})

    def _validate_capacity(self):
        if self.capacity < 1:
            raise ValidationError({"capacity": "Capacidade deve ser maior que zero."})

    def __str__(self):
        return self.name


class ClassSession(BaseModel):
    STATUS_SCHEDULED = "SCHEDULED"
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = (
        (STATUS_SCHEDULED, "Agendada"),
        (STATUS_OPEN, "Aberta"),
        (STATUS_CLOSED, "Encerrada"),
        (STATUS_CANCELLED, "Cancelada"),
    )

    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opened_sessions",
    )
    closed_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_sessions",
    )

    class Meta:
        ordering = ("-starts_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("class_group", "starts_at"),
                name="uniq_class_group_session_start",
            )
        ]

    def clean(self):
        super().clean()
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Encerramento da sessao deve ocorrer depois do inicio."})

    def open(self, actor):
        if self.status not in {self.STATUS_SCHEDULED, self.STATUS_CLOSED}:
            raise ValidationError("Sessao nao pode ser aberta neste estado.")
        self.status = self.STATUS_OPEN
        self.opened_at = timezone.now()
        self.opened_by = actor

    def close(self, actor):
        if self.status != self.STATUS_OPEN:
            raise ValidationError("Somente sessoes abertas podem ser encerradas.")
        self.status = self.STATUS_CLOSED
        self.closed_at = timezone.now()
        self.closed_by = actor

    def __str__(self):
        return f"{self.class_group.name} - {self.starts_at:%d/%m/%Y %H:%M}"
