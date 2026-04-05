from django.core.exceptions import ValidationError
from django.db import models

from .category import ClassCategory
from .common import TimeStampedModel
from .person import Person


class ClassGroup(TimeStampedModel):
    code = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    class_category = models.ForeignKey(
        ClassCategory,
        on_delete=models.PROTECT,
        related_name="class_groups",
    )
    main_teacher = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="primary_class_groups",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    default_capacity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.display_name} - {self.class_category.display_name}"

    def clean(self):
        if self.main_teacher_id and not self.main_teacher.has_type_code("instructor"):
            raise ValidationError(
                {
                    "main_teacher": (
                        "A turma deve possuir um professor principal com o tipo Professor."
                    )
                }
            )
