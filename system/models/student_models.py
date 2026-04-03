from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from system.models.base import BaseModel
from system.models.identity_models import SystemUser


class StudentProfile(BaseModel):
    TYPE_HOLDER = "holder"
    TYPE_DEPENDENT = "dependent"

    STATUS_PENDING = "PENDING"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_PENDING_FINANCIAL = "PENDING_FINANCIAL"
    STATUS_PAUSED = "PAUSED"
    STATUS_BLOCKED = "BLOCKED"
    STATUS_INACTIVE = "INACTIVE"

    TYPE_CHOICES = (
        (TYPE_HOLDER, "Titular"),
        (TYPE_DEPENDENT, "Dependente"),
    )
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pendente"),
        (STATUS_ACTIVE, "Ativo"),
        (STATUS_PENDING_FINANCIAL, "Pendente Financeiro"),
        (STATUS_PAUSED, "Pausado"),
        (STATUS_BLOCKED, "Bloqueado"),
        (STATUS_INACTIVE, "Inativo"),
    )

    user = models.OneToOneField(
        SystemUser,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    operational_status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    birth_date = models.DateField(null=True, blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    join_date = models.DateField(default=timezone.localdate)
    self_service_access = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("user__full_name", "user__cpf")

    def clean(self):
        super().clean()
        if self.student_type == self.TYPE_HOLDER:
            self.self_service_access = True

    @property
    def is_dependent(self):
        return self.student_type == self.TYPE_DEPENDENT

    @property
    def primary_guardian_link(self):
        queryset = self.guardian_links.filter(end_date__isnull=True, is_primary=True)
        return queryset.select_related("responsible_user").first()

    def __str__(self):
        return f"{self.user.full_name} - {self.get_student_type_display()}"


class GuardianRelationship(BaseModel):
    RELATIONSHIP_SELF = "self"
    RELATIONSHIP_PARENT = "parent"
    RELATIONSHIP_MOTHER = "mother"
    RELATIONSHIP_FATHER = "father"
    RELATIONSHIP_GUARDIAN = "guardian"
    RELATIONSHIP_SPOUSE = "spouse"
    RELATIONSHIP_OTHER = "other"

    RELATIONSHIP_CHOICES = (
        (RELATIONSHIP_SELF, "Proprio"),
        (RELATIONSHIP_PARENT, "Responsavel"),
        (RELATIONSHIP_MOTHER, "Mae"),
        (RELATIONSHIP_FATHER, "Pai"),
        (RELATIONSHIP_GUARDIAN, "Guardiao legal"),
        (RELATIONSHIP_SPOUSE, "Conjuge"),
        (RELATIONSHIP_OTHER, "Outro"),
    )

    responsible_user = models.ForeignKey(
        SystemUser,
        on_delete=models.CASCADE,
        related_name="dependent_links_as_responsible",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="guardian_links",
    )
    relationship_type = models.CharField(max_length=24, choices=RELATIONSHIP_CHOICES)
    is_financial_responsible = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("student__user__full_name", "responsible_user__full_name")
        constraints = [
            models.UniqueConstraint(
                fields=("responsible_user", "student", "start_date"),
                name="uniq_guardian_relationship_period",
            )
        ]

    def clean(self):
        super().clean()
        self._validate_dates()
        self._validate_relationship_consistency()
        self._validate_primary_guardian_uniqueness()

    def _validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "A data final nao pode ser anterior ao inicio."})

    def _validate_relationship_consistency(self):
        same_identity = self.student.user_id == self.responsible_user_id
        if same_identity and self.relationship_type != self.RELATIONSHIP_SELF:
            raise ValidationError({"relationship_type": "Titular deve usar vinculo proprio."})
        if not same_identity and self.relationship_type == self.RELATIONSHIP_SELF:
            raise ValidationError({"relationship_type": "Dependente nao pode usar vinculo proprio."})

    def _validate_primary_guardian_uniqueness(self):
        if self.end_date is not None or not self.is_primary:
            return
        queryset = GuardianRelationship.objects.exclude(pk=self.pk)
        queryset = queryset.filter(student=self.student, end_date__isnull=True, is_primary=True)
        if queryset.exists():
            raise ValidationError({"is_primary": "Ja existe um responsavel primario ativo."})

    @property
    def is_active(self):
        return self.end_date is None

    def __str__(self):
        return f"{self.responsible_user.full_name} -> {self.student.user.full_name}"


class EmergencyRecord(BaseModel):
    student = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="emergency_record",
    )
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_phone = models.CharField(max_length=32)
    emergency_contact_relationship = models.CharField(max_length=128)
    blood_type = models.CharField(max_length=16, blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    medical_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("student__user__full_name",)

    def __str__(self):
        return f"Prontuario de {self.student.user.full_name}"
