import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from system.models.base import BaseModel


class ClassReservation(BaseModel):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CONSUMED = "CONSUMED"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Ativa"),
        (STATUS_CANCELLED, "Cancelada"),
        (STATUS_CONSUMED, "Consumida"),
    )

    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    session = models.ForeignKey(
        "system.ClassSession",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "session"),
                name="uniq_student_session_reservation",
            )
        ]

    def __str__(self):
        return f"{self.student.user.full_name} - {self.session}"


class AttendanceQrToken(BaseModel):
    session = models.ForeignKey(
        "system.ClassSession",
        on_delete=models.CASCADE,
        related_name="qr_tokens",
    )
    token = models.CharField(max_length=96, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    generated_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_qr_tokens",
    )

    class Meta:
        ordering = ("-created_at",)

    @classmethod
    def issue(cls, *, session, generated_by, ttl_seconds):
        return cls.objects.create(
            session=session,
            token=secrets.token_urlsafe(24),
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
            generated_by=generated_by,
        )

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


class PhysicalAttendance(BaseModel):
    METHOD_QR = "QR"
    METHOD_MANUAL = "MANUAL"

    METHOD_CHOICES = (
        (METHOD_QR, "QR"),
        (METHOD_MANUAL, "Manual"),
    )

    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    session = models.ForeignKey(
        "system.ClassSession",
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    reservation = models.ForeignKey(
        ClassReservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendances",
    )
    checkin_method = models.CharField(max_length=16, choices=METHOD_CHOICES)
    checked_in_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendances",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-checked_in_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "session"),
                name="uniq_student_session_attendance",
            )
        ]

    def __str__(self):
        return f"{self.student.user.full_name} - {self.session}"


class AttendanceAttempt(BaseModel):
    STATUS_ALLOWED = "ALLOWED"
    STATUS_DENIED = "DENIED"
    STATUS_DUPLICATE = "DUPLICATE"

    STATUS_CHOICES = (
        (STATUS_ALLOWED, "Permitido"),
        (STATUS_DENIED, "Negado"),
        (STATUS_DUPLICATE, "Duplicado"),
    )

    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendance_attempts",
    )
    session = models.ForeignKey(
        "system.ClassSession",
        on_delete=models.CASCADE,
        related_name="attendance_attempts",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    reason = models.CharField(max_length=255)
    token_value = models.CharField(max_length=96, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.student.user.full_name} - {self.status}"
