from django.core.exceptions import ValidationError
from django.db import models

from system.models.base import BaseModel


class AcademyConfiguration(BaseModel):
    singleton_key = models.CharField(max_length=32, default="default", unique=True, editable=False)
    academy_name = models.CharField(max_length=120, default="LV JIU JITSU")
    hero_title = models.CharField(max_length=160, default="Jiu-Jitsu com metodo, disciplina e comunidade.")
    hero_subtitle = models.TextField(
        default="Construa constancia, evolucao tecnica e confianca em um ambiente acolhedor para iniciantes e atletas."
    )
    public_whatsapp = models.CharField(max_length=32, blank=True)
    public_email = models.EmailField(blank=True)
    public_instagram = models.CharField(max_length=120, blank=True)
    public_address = models.CharField(max_length=255, blank=True)
    dependent_credential_min_age = models.PositiveSmallIntegerField(default=12)
    qr_code_ttl_seconds = models.PositiveIntegerField(default=60)
    late_arrival_tolerance_minutes = models.PositiveIntegerField(default=10)
    trial_class_minimum_notice_hours = models.PositiveIntegerField(default=4)
    allow_trial_without_guardian = models.BooleanField(default=False)
    public_notice = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Academy Configuration"
        verbose_name_plural = "Academy Configuration"

    def clean(self):
        super().clean()
        self.singleton_key = "default"
        if not self.is_active:
            raise ValidationError({"is_active": "A configuracao global precisa permanecer ativa."})

    def save(self, *args, **kwargs):
        self.singleton_key = "default"
        self.is_active = True
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.academy_name
