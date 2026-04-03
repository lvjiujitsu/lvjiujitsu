from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from system.models.base import BaseModel


class PublicPlan(BaseModel):
    BILLING_MONTHLY = "monthly"
    BILLING_QUARTERLY = "quarterly"
    BILLING_SEMIANNUAL = "semiannual"
    BILLING_ANNUAL = "annual"

    BILLING_CYCLE_CHOICES = (
        (BILLING_MONTHLY, "Mensal"),
        (BILLING_QUARTERLY, "Trimestral"),
        (BILLING_SEMIANNUAL, "Semestral"),
        (BILLING_ANNUAL, "Anual"),
    )

    name = models.CharField(max_length=120)
    summary = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    billing_cycle = models.CharField(max_length=16, choices=BILLING_CYCLE_CHOICES, default=BILLING_MONTHLY)
    cta_label = models.CharField(max_length=64, default="Quero saber mais")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        return self.name

    @property
    def public_price(self):
        return f"R$ {self.amount:.2f}".replace(".", ",")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PublicClassSchedule(BaseModel):
    WEEKDAY_MONDAY = 1
    WEEKDAY_TUESDAY = 2
    WEEKDAY_WEDNESDAY = 3
    WEEKDAY_THURSDAY = 4
    WEEKDAY_FRIDAY = 5
    WEEKDAY_SATURDAY = 6
    WEEKDAY_SUNDAY = 7

    WEEKDAY_CHOICES = (
        (WEEKDAY_MONDAY, "Segunda"),
        (WEEKDAY_TUESDAY, "Terca"),
        (WEEKDAY_WEDNESDAY, "Quarta"),
        (WEEKDAY_THURSDAY, "Quinta"),
        (WEEKDAY_FRIDAY, "Sexta"),
        (WEEKDAY_SATURDAY, "Sabado"),
        (WEEKDAY_SUNDAY, "Domingo"),
    )

    class_level = models.CharField(max_length=80)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    instructor_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("weekday", "start_time", "display_order")

    def __str__(self):
        return f"{self.get_weekday_display()} - {self.class_level}"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Lead(BaseModel):
    SOURCE_LANDING = "landing"
    SOURCE_INSTAGRAM = "instagram"
    SOURCE_WHATSAPP = "whatsapp"
    SOURCE_REFERRAL = "referral"
    SOURCE_WALKIN = "walkin"

    SOURCE_CHOICES = (
        (SOURCE_LANDING, "Landing"),
        (SOURCE_INSTAGRAM, "Instagram"),
        (SOURCE_WHATSAPP, "WhatsApp"),
        (SOURCE_REFERRAL, "Indicacao"),
        (SOURCE_WALKIN, "Presencial"),
    )

    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_CONVERTED = "converted"
    STATUS_ARCHIVED = "archived"

    STATUS_CHOICES = (
        (STATUS_NEW, "Novo"),
        (STATUS_CONTACTED, "Em contato"),
        (STATUS_CONVERTED, "Convertido"),
        (STATUS_ARCHIVED, "Arquivado"),
    )

    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_LANDING)
    interest_note = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_NEW)
    requested_plan = models.ForeignKey(
        PublicPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    converted_user = models.ForeignKey(
        "system.SystemUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converted_leads",
    )

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if not self.email and not self.phone:
            raise ValidationError("Informe ao menos e-mail ou telefone.")

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TrialClassRequest(BaseModel):
    PERIOD_MORNING = "morning"
    PERIOD_AFTERNOON = "afternoon"
    PERIOD_EVENING = "evening"

    PERIOD_CHOICES = (
        (PERIOD_MORNING, "Manha"),
        (PERIOD_AFTERNOON, "Tarde"),
        (PERIOD_EVENING, "Noite"),
    )

    STATUS_REQUESTED = "requested"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_REQUESTED, "Solicitada"),
        (STATUS_CONFIRMED, "Confirmada"),
        (STATUS_COMPLETED, "Concluida"),
        (STATUS_CANCELLED, "Cancelada"),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="trial_class_requests")
    preferred_date = models.DateField()
    preferred_period = models.CharField(max_length=16, choices=PERIOD_CHOICES)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_REQUESTED)

    class Meta:
        ordering = ("preferred_date", "-created_at")

    def clean(self):
        super().clean()
        if self.preferred_date < timezone.localdate():
            raise ValidationError({"preferred_date": "A aula experimental precisa ser solicitada para hoje ou futuro."})

    def __str__(self):
        return f"{self.lead.full_name} - {self.preferred_date}"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
