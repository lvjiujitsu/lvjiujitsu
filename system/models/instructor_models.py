from django.db import models

from system.models.base import BaseModel
from system.models.identity_models import SystemUser


class InstructorProfile(BaseModel):
    user = models.OneToOneField(
        SystemUser,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    belt_rank = models.ForeignKey(
        "system.IbjjfBelt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instructors",
    )
    bio = models.TextField(blank=True)
    specialties = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("user__full_name",)

    def __str__(self):
        return self.user.full_name
