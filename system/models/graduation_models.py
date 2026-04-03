import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from system.models.base import BaseModel


class GraduationRule(BaseModel):
    SCOPE_OFFICIAL = "OFFICIAL"
    SCOPE_INTERNAL = "INTERNAL"

    SCOPE_CHOICES = (
        (SCOPE_OFFICIAL, "Referencia oficial"),
        (SCOPE_INTERNAL, "Regra interna da academia"),
    )

    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES)
    discipline = models.ForeignKey(
        "system.ClassDiscipline",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graduation_rules",
    )
    current_belt = models.ForeignKey(
        "system.IbjjfBelt",
        on_delete=models.CASCADE,
        related_name="graduation_rules_as_current",
    )
    current_degree = models.PositiveSmallIntegerField(default=0)
    target_belt = models.ForeignKey(
        "system.IbjjfBelt",
        on_delete=models.CASCADE,
        related_name="graduation_rules_as_target",
    )
    target_degree = models.PositiveSmallIntegerField(default=0)
    minimum_active_days = models.PositiveIntegerField(default=0)
    minimum_attendances = models.PositiveIntegerField(default=0)
    minimum_age = models.PositiveIntegerField(default=0)
    maximum_inactivity_days = models.PositiveIntegerField(default=45)
    requires_exam = models.BooleanField(default=True)
    criteria_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("scope", "current_belt__display_order", "current_degree", "target_belt__display_order", "target_degree")
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "discipline", "current_belt", "current_degree"),
                name="uniq_graduation_rule_scope_stage",
            ),
            models.UniqueConstraint(
                fields=("scope", "current_belt", "current_degree"),
                condition=Q(discipline__isnull=True),
                name="uniq_graduation_rule_scope_stage_generic",
            ),
        ]

    def clean(self):
        super().clean()
        if self.current_degree > 4 or self.target_degree > 4:
            raise ValidationError("O grau configurado deve ficar entre 0 e 4.")
        if self.maximum_inactivity_days < 1:
            raise ValidationError({"maximum_inactivity_days": "A janela maxima de inatividade deve ser positiva."})
        if self.minimum_active_days < self.minimum_attendances:
            raise ValidationError({"minimum_active_days": "Tempo ativo nao pode ser menor que a frequencia minima."})
        if self._compare_stage(self.current_belt, self.current_degree, self.target_belt, self.target_degree) >= 0:
            raise ValidationError("A etapa alvo deve ser superior a etapa atual.")

    def _compare_stage(self, current_belt, current_degree, target_belt, target_degree):
        current_key = (current_belt.display_order, current_degree)
        target_key = (target_belt.display_order, target_degree)
        return (current_key > target_key) - (current_key < target_key)

    def __str__(self):
        return f"{self.get_scope_display()} - {self.current_belt.name}/{self.current_degree} -> {self.target_belt.name}/{self.target_degree}"


class GraduationHistory(BaseModel):
    EVENT_INITIAL = "INITIAL"
    EVENT_PROMOTION = "PROMOTION"
    EVENT_MANUAL = "MANUAL"

    EVENT_CHOICES = (
        (EVENT_INITIAL, "Inicio da jornada"),
        (EVENT_PROMOTION, "Promocao"),
        (EVENT_MANUAL, "Ajuste manual"),
    )

    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="graduation_histories",
    )
    belt_rank = models.ForeignKey(
        "system.IbjjfBelt",
        on_delete=models.PROTECT,
        related_name="graduation_histories",
    )
    degree_level = models.PositiveSmallIntegerField(default=0)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    event_type = models.CharField(max_length=16, choices=EVENT_CHOICES, default=EVENT_INITIAL)
    recorded_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_graduation_histories",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("student__user__full_name", "-started_on", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("student",),
                condition=Q(is_current=True),
                name="uniq_current_graduation_history_per_student",
            )
        ]

    def clean(self):
        super().clean()
        if self.degree_level > 4:
            raise ValidationError({"degree_level": "O grau deve ficar entre 0 e 4."})
        if self.ended_on and self.ended_on < self.started_on:
            raise ValidationError({"ended_on": "A data final nao pode ser anterior ao inicio."})
        if self.is_current and self.ended_on is not None:
            raise ValidationError({"ended_on": "Historico atual nao pode possuir data final."})
        if not self.is_current and self.ended_on is None:
            raise ValidationError({"ended_on": "Historico encerrado exige data final."})

    @property
    def stage_label(self):
        return f"{self.belt_rank.name} - Grau {self.degree_level}"

    def __str__(self):
        return f"{self.student.user.full_name} - {self.stage_label}"


class GraduationExam(BaseModel):
    STATUS_OPEN = "OPEN"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = (
        (STATUS_OPEN, "Aberto"),
        (STATUS_COMPLETED, "Concluido"),
        (STATUS_CANCELLED, "Cancelado"),
    )

    title = models.CharField(max_length=255)
    scheduled_for = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    discipline = models.ForeignKey(
        "system.ClassDiscipline",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graduation_exams",
    )
    class_group = models.ForeignKey(
        "system.ClassGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graduation_exams",
    )
    created_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_graduation_exams",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-scheduled_for", "-created_at")

    def __str__(self):
        return self.title


class GraduationExamParticipation(BaseModel):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_POSTPONED = "POSTPONED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pendente"),
        (STATUS_APPROVED, "Aprovado"),
        (STATUS_POSTPONED, "Adiado"),
        (STATUS_REJECTED, "Nao aprovado"),
    )

    exam = models.ForeignKey(
        GraduationExam,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    student = models.ForeignKey(
        "system.StudentProfile",
        on_delete=models.CASCADE,
        related_name="graduation_exam_participations",
    )
    current_belt = models.ForeignKey(
        "system.IbjjfBelt",
        on_delete=models.PROTECT,
        related_name="graduation_exam_participations_as_current",
    )
    current_degree = models.PositiveSmallIntegerField(default=0)
    suggested_belt = models.ForeignKey(
        "system.IbjjfBelt",
        on_delete=models.PROTECT,
        related_name="graduation_exam_participations_as_suggested",
    )
    suggested_degree = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    eligibility_snapshot = models.JSONField(default=dict, blank=True)
    decided_by = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graduation_exam_decisions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    promoted_history = models.ForeignKey(
        GraduationHistory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="originating_participations",
    )
    certificate_code = models.CharField(max_length=32, blank=True, null=True, unique=True)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("student__user__full_name",)
        constraints = [
            models.UniqueConstraint(
                fields=("exam", "student"),
                name="uniq_graduation_exam_student",
            )
        ]

    def clean(self):
        super().clean()
        if self.current_degree > 4 or self.suggested_degree > 4:
            raise ValidationError("O grau do exame deve ficar entre 0 e 4.")

    def issue_certificate_code(self):
        if self.certificate_code:
            return self.certificate_code
        return f"GRAD-{timezone.localdate():%Y%m%d}-{secrets.token_hex(4).upper()}"

    @property
    def current_stage_label(self):
        return f"{self.current_belt.name} - Grau {self.current_degree}"

    @property
    def suggested_stage_label(self):
        return f"{self.suggested_belt.name} - Grau {self.suggested_degree}"

    def __str__(self):
        return f"{self.exam.title} - {self.student.user.full_name}"
