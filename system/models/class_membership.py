from django.core.exceptions import ValidationError
from django.db import models

from .class_group import ClassGroup
from .common import TimeStampedModel
from .person import Person


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Ativa"
    PAUSED = "paused", "Pausada"
    CANCELLED = "cancelled", "Cancelada"


class ClassInstructorAssignment(TimeStampedModel):
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="instructor_assignments",
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="class_instructor_assignments",
    )
    is_primary = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("class_group__display_name", "person__full_name")
        constraints = [
            models.UniqueConstraint(
                fields=("class_group", "person"),
                name="unique_class_instructor_assignment",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.person.full_name} -> {self.class_group.display_name}"

    def clean(self):
        if self.is_primary:
            raise ValidationError(
                {
                    "is_primary": (
                        "Professor principal deve ser definido diretamente na turma, "
                        "não no vínculo de instrutor auxiliar."
                    )
                }
            )
        if self.person_id and not self.person.has_type_code(
            "administrative-assistant",
            "instructor",
        ):
            raise ValidationError(
                {
                    "person": (
                        "A pessoa precisa possuir o tipo Administrativo ou Professor "
                        "para atuar como apoio/instrutor auxiliar da turma."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ClassEnrollment(TimeStampedModel):
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="class_enrollments",
    )
    status = models.CharField(
        max_length=16,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("class_group__display_name", "person__full_name")
        constraints = [
            models.UniqueConstraint(
                fields=("class_group", "person"),
                name="unique_class_enrollment",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.person.full_name} matriculado em {self.class_group.display_name}"

    def clean(self):
        if self.person_id and not self.person.has_type_code("student", "dependent"):
            raise ValidationError(
                {"person": "A pessoa precisa possuir o tipo Aluno ou Dependente para entrar na turma."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
