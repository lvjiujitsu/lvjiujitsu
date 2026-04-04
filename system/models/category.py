from django.db import models

from .common import TimeStampedModel


class CategoryAudience(models.TextChoices):
    ADULT = "adult", "Adulto"
    JUVENILE = "juvenile", "Juvenil"
    KIDS = "kids", "Kids"
    WOMEN = "women", "Feminino"


class ClassCategory(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    display_name = models.CharField(max_length=80, unique=True)
    audience = models.CharField(max_length=16, choices=CategoryAudience.choices)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "display_name")

    def __str__(self) -> str:
        return self.display_name


class IbjjfAgeCategory(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    display_name = models.CharField(max_length=120, unique=True)
    audience = models.CharField(max_length=16, choices=CategoryAudience.choices)
    minimum_age = models.PositiveIntegerField()
    maximum_age = models.PositiveIntegerField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "minimum_age", "display_name")

    def __str__(self) -> str:
        return self.display_name

    def matches_age(self, age: int) -> bool:
        if age < self.minimum_age:
            return False
        if self.maximum_age is None:
            return True
        return age <= self.maximum_age
