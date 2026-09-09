from django.db import models
from django.db.models import Q

from .class_schedule import TrainingStyle, WeekdayCode
from system.core.models import TimeStampedModel


class AdministrativeAccessRequestStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Recusada"
    CANCELED = "canceled", "Cancelada"


class AdministrativeAccessRequestOrigin(models.TextChoices):
    PUBLIC_REGISTRATION = "public_registration", "Cadastro público"
    PORTAL = "portal", "Portal"
    ADMIN_CREATED = "admin_created", "Criada pela gestão"


class AdministrativeAccessRequest(TimeStampedModel):
    status = models.CharField(
        max_length=16,
        choices=AdministrativeAccessRequestStatus.choices,
        default=AdministrativeAccessRequestStatus.PENDING,
    )
    origin = models.CharField(
        max_length=32,
        choices=AdministrativeAccessRequestOrigin.choices,
        default=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
    )
    person = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="administrative_access_requests",
        null=True,
        blank=True,
    )
    approved_person = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="approved_administrative_access_requests",
        null=True,
        blank=True,
    )
    decided_by = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="decided_administrative_access_requests",
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    requested_role_codes = models.JSONField(default=list, blank=True)
    approved_role_codes = models.JSONField(default=list, blank=True)
    grant_full_administrative = models.BooleanField(default=False)
    justification = models.TextField()
    request_payload = models.JSONField(default=dict, blank=True)
    decision_notes = models.TextField(blank=True)
    password_hash = models.CharField(max_length=255, blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("cpf",),
                condition=Q(status=AdministrativeAccessRequestStatus.PENDING),
                name="unique_pending_admin_access_request_per_cpf",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.get_status_display()}"


class ClassCatalogRequestStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Recusada"
    CANCELED = "canceled", "Cancelada"


class ClassCatalogRequestType(models.TextChoices):
    NEW_SCHEDULE = "new_schedule", "Novo horário"
    NEW_CLASS_GROUP = "new_class_group", "Nova turma"
    NEW_TEACHER_WITH_SCHEDULE = "new_teacher_with_schedule", "Professor novo com horário"
    TEACHER_JOIN_EXISTING_CLASS = (
        "teacher_join_existing_class",
        "Professor novo em turma existente",
    )


class ClassCatalogRequestOrigin(models.TextChoices):
    PORTAL = "portal", "Portal"
    PUBLIC_REGISTRATION = "public_registration", "Cadastro público"
    ADMIN_CREATED = "admin_created", "Criada pela gestão"


class ClassCatalogRequest(TimeStampedModel):
    status = models.CharField(
        max_length=16,
        choices=ClassCatalogRequestStatus.choices,
        default=ClassCatalogRequestStatus.PENDING,
    )
    request_type = models.CharField(
        max_length=32,
        choices=ClassCatalogRequestType.choices,
    )
    origin = models.CharField(
        max_length=32,
        choices=ClassCatalogRequestOrigin.choices,
        default=ClassCatalogRequestOrigin.PORTAL,
    )
    requester_person = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="class_catalog_requests",
        null=True,
        blank=True,
    )
    teacher_person = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="teacher_class_catalog_requests",
        null=True,
        blank=True,
    )
    created_teacher = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="created_from_class_catalog_requests",
        null=True,
        blank=True,
    )
    decided_by = models.ForeignKey(
        "business_rule.Person",
        on_delete=models.SET_NULL,
        related_name="decided_class_catalog_requests",
        null=True,
        blank=True,
    )
    target_class_group = models.ForeignKey(
        "business_rule.ClassGroup",
        on_delete=models.SET_NULL,
        related_name="targeted_class_catalog_requests",
        null=True,
        blank=True,
    )
    created_class_group = models.ForeignKey(
        "business_rule.ClassGroup",
        on_delete=models.SET_NULL,
        related_name="created_from_class_catalog_requests",
        null=True,
        blank=True,
    )
    class_category = models.ForeignKey(
        "business_rule.ClassCategory",
        on_delete=models.SET_NULL,
        related_name="class_catalog_requests",
        null=True,
        blank=True,
    )
    display_name = models.CharField(max_length=120, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    cpf = models.CharField(max_length=14, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    password_hash = models.CharField(max_length=255, blank=True, default="")
    martial_art = models.CharField(max_length=24, blank=True)
    martial_art_graduation = models.CharField(max_length=120, blank=True)
    jiu_jitsu_belt = models.CharField(max_length=24, blank=True)
    jiu_jitsu_stripes = models.PositiveSmallIntegerField(null=True, blank=True)
    weekday = models.CharField(max_length=12, choices=WeekdayCode.choices, blank=True)
    training_style = models.CharField(max_length=12, choices=TrainingStyle.choices, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    default_capacity = models.PositiveIntegerField(default=0)
    extra_schedules = models.JSONField(default=list, blank=True)
    justification = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    approved_payload = models.JSONField(default=dict, blank=True)
    decision_notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        label = self.full_name or getattr(self.teacher_person, "full_name", "") or self.display_name
        return f"{label} - {self.get_request_type_display()} - {self.get_status_display()}"
