from django.core.exceptions import ValidationError
from django.db import models

from .category import ClassCategory
from .common import TimeStampedModel
from .person import Person


class ClassAudience(models.TextChoices):
    ADULT = "adult", "Adulto"
    KIDS = "kids", "Kids"
    JUVENILE = "juvenile", "Juvenil"
    WOMEN = "women", "Feminino"


class ClassGroup(TimeStampedModel):
    code = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    audience = models.CharField(
        max_length=20,
        choices=ClassAudience.choices,
        default=ClassAudience.ADULT,
    )
    class_category = models.ForeignKey(
        ClassCategory,
        on_delete=models.PROTECT,
        related_name="class_groups",
        null=True,
        blank=True,
    )
    main_teacher = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="primary_class_groups",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    default_capacity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("audience", "code")

    def __str__(self) -> str:
        if self.class_category_id:
            return f"{self.display_name} - {self.class_category.display_name}"
        return self.display_name

    @property
    def public_label(self) -> str:
        if self.class_category_id:
            return self.class_category.display_name
        return self.get_audience_display()

    def clean(self):
        if (
            self.class_category_id
            and self.class_category.audience != self.audience
        ):
            raise ValidationError(
                {
                    "class_category": (
                        "A categoria da turma deve pertencer ao mesmo público da turma."
                    )
                }
            )
        if self.main_teacher_id and not self.main_teacher.has_type_code("instructor"):
            raise ValidationError(
                {
                    "main_teacher": (
                        "A turma deve possuir um professor principal com o tipo Professor."
                    )
                }
            )
