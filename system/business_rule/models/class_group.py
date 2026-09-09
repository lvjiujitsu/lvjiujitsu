from django.core.exceptions import ValidationError
from django.db import models

from .category import ClassCategory
from system.core.models import TimeStampedModel
from .person import Person
from system.business_rule.constants import PersonTypeCode


class ClassGroup(TimeStampedModel):
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
        ordering = ("class_category__display_order", "class_category__display_name", "main_teacher__full_name", "display_name")

    def __str__(self) -> str:
        return f"{self.display_name} - {self.class_category.display_name}"

    def clean(self):
        if self.main_teacher_id and not self.main_teacher.has_type_code(PersonTypeCode.INSTRUCTOR):
            raise ValidationError(
                {
                    "main_teacher": (
                        "A turma deve possuir um professor principal com o tipo Professor."
                    )
                }
            )
