from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PersonType(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    display_name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_name",)

    def __str__(self) -> str:
        return self.display_name


class Person(TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person_profile",
    )
    full_name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    person_types = models.ManyToManyField(
        PersonType,
        through="PersonTypeAssignment",
        related_name="people",
    )

    class Meta:
        ordering = ("full_name",)

    def __str__(self) -> str:
        return self.full_name


class PersonTypeAssignment(TimeStampedModel):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="type_assignments",
    )
    person_type = models.ForeignKey(
        PersonType,
        on_delete=models.CASCADE,
        related_name="person_assignments",
    )

    class Meta:
        ordering = ("person__full_name", "person_type__display_name")
        constraints = [
            models.UniqueConstraint(
                fields=("person", "person_type"),
                name="unique_person_type_assignment",
            )
        ]

    def __str__(self) -> str:
        return f"{self.person.full_name} - {self.person_type.display_name}"
