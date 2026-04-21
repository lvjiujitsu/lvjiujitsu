from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .category import CategoryAudience, IbjjfAgeCategory
from .class_group import ClassGroup
from .common import TimeStampedModel
from .person import BiologicalSex, Person
from system.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES, CLASS_STAFF_PERSON_TYPE_CODES


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Ativa"
    PAUSED = "paused", "Pausada"
    CANCELLED = "cancelled", "Cancelada"


def get_class_group_eligibility_error(*, birth_date, biological_sex, class_group):
    if class_group is None:
        return None
    audience = _resolve_birth_date_audience(birth_date)
    if audience is None:
        return "Informe a data de nascimento para validar a turma escolhida."
    if class_group.class_category.audience == CategoryAudience.WOMEN:
        return _get_women_group_error(audience, biological_sex)
    if _is_child_cross_category_allowed(audience, class_group.class_category.audience):
        return None
    if audience != class_group.class_category.audience:
        return "A turma escolhida não é compatível com a faixa etária da pessoa."
    return None


def get_person_class_group_eligibility_error(person, class_group):
    return get_class_group_eligibility_error(
        birth_date=person.birth_date,
        biological_sex=person.biological_sex,
        class_group=class_group,
    )


def _resolve_birth_date_audience(birth_date):
    if not birth_date:
        return None
    age = _get_age_from_birth_date(birth_date)
    categories = IbjjfAgeCategory.objects.filter(is_active=True).order_by(
        "display_order",
        "minimum_age",
    )
    for category in categories:
        if category.matches_age(age):
            return category.audience
    return None


def _get_age_from_birth_date(birth_date):
    reference = timezone.localdate()
    age = reference.year - birth_date.year
    has_had_birthday = (reference.month, reference.day) >= (
        birth_date.month,
        birth_date.day,
    )
    return age if has_had_birthday else age - 1


def _get_women_group_error(audience, biological_sex):
    if biological_sex != BiologicalSex.FEMALE:
        return "A turma feminina aceita apenas alunas do sexo biológico feminino."
    if audience != CategoryAudience.ADULT:
        return "A turma feminina está liberada apenas para alunas adultas."
    return None


def _is_child_cross_category_allowed(person_audience, group_audience):
    child_audiences = {CategoryAudience.KIDS, CategoryAudience.JUVENILE}
    return person_audience in child_audiences and group_audience in child_audiences


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
        if self.person_id and not self.person.has_type_code(*CLASS_STAFF_PERSON_TYPE_CODES):
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
        self._validate_student_type()
        self._validate_class_group_eligibility()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def _validate_student_type(self):
        if self.person_id and not self.person.has_type_code(
            *CLASS_ENROLLMENT_PERSON_TYPE_CODES
        ):
            raise ValidationError(
                {"person": "A pessoa precisa possuir o tipo Aluno ou Dependente para entrar na turma."}
            )

    def _validate_class_group_eligibility(self):
        if not self.person_id or not self.class_group_id:
            return
        error = get_person_class_group_eligibility_error(self.person, self.class_group)
        if error:
            raise ValidationError({"class_group": error})
