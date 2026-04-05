from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .common import TimeStampedModel


class PersonType(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    display_name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_name",)

    def __str__(self) -> str:
        return self.display_name


class BloodType(models.TextChoices):
    A_POSITIVE = "A+", "A+"
    A_NEGATIVE = "A-", "A-"
    B_POSITIVE = "B+", "B+"
    B_NEGATIVE = "B-", "B-"
    AB_POSITIVE = "AB+", "AB+"
    AB_NEGATIVE = "AB-", "AB-"
    O_POSITIVE = "O+", "O+"
    O_NEGATIVE = "O-", "O-"


class BiologicalSex(models.TextChoices):
    MALE = "male", "Masculino"
    FEMALE = "female", "Feminino"


class Person(TimeStampedModel):
    full_name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    biological_sex = models.CharField(
        max_length=16,
        choices=BiologicalSex.choices,
        blank=True,
    )
    blood_type = models.CharField(max_length=3, choices=BloodType.choices, blank=True)
    allergies = models.TextField(blank=True)
    previous_injuries = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    person_type = models.ForeignKey(
        PersonType,
        on_delete=models.PROTECT,
        related_name="people",
        null=True,
        blank=True,
    )
    class_category = models.ForeignKey(
        "system.ClassCategory",
        on_delete=models.SET_NULL,
        related_name="people",
        null=True,
        blank=True,
    )
    class_group = models.ForeignKey(
        "system.ClassGroup",
        on_delete=models.SET_NULL,
        related_name="people",
        null=True,
        blank=True,
    )
    class_schedule = models.ForeignKey(
        "system.ClassSchedule",
        on_delete=models.SET_NULL,
        related_name="people",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("full_name",)

    def __str__(self) -> str:
        return self.full_name

    def has_type_code(self, *codes: str) -> bool:
        if not self.person_type_id:
            return False
        return self.person_type.code in codes

    @property
    def has_portal_access(self) -> bool:
        return hasattr(self, "access_account")

    def get_age(self, reference_date=None):
        if not self.birth_date:
            return None

        reference = reference_date or timezone.localdate()
        age = reference.year - self.birth_date.year
        has_had_birthday = (reference.month, reference.day) >= (
            self.birth_date.month,
            self.birth_date.day,
        )
        return age if has_had_birthday else age - 1

    @property
    def current_ibjjf_category(self):
        age = self.get_age()
        if age is None:
            return None

        from .category import IbjjfAgeCategory

        categories = IbjjfAgeCategory.objects.filter(is_active=True).order_by("display_order")
        for category in categories:
            if category.matches_age(age):
                return category
        return None


class PortalAccount(TimeStampedModel):
    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name="access_account",
    )
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_login_at = models.DateTimeField(null=True, blank=True)
    password_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("person__full_name",)

    def __str__(self) -> str:
        return self.person.full_name

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)
        self.password_updated_at = timezone.now()

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)

    def register_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.last_login_at = timezone.now()
        self.save(update_fields=("failed_login_attempts", "last_login_at", "updated_at"))

    def register_failed_login(self) -> None:
        self.failed_login_attempts += 1
        self.save(update_fields=("failed_login_attempts", "updated_at"))


class PersonRelationshipKind(models.TextChoices):
    RESPONSIBLE_FOR = "responsible_for", "Responsável por"


class PersonRelationship(TimeStampedModel):
    source_person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_kind = models.CharField(
        max_length=40,
        choices=PersonRelationshipKind.choices,
        default=PersonRelationshipKind.RESPONSIBLE_FOR,
    )
    kinship_type = models.CharField(max_length=24, blank=True)
    kinship_other_label = models.CharField(max_length=80, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("source_person__full_name", "target_person__full_name")
        constraints = [
            models.UniqueConstraint(
                fields=("source_person", "target_person", "relationship_kind"),
                name="unique_person_relationship",
            ),
            models.CheckConstraint(
                check=~Q(source_person=F("target_person")),
                name="prevent_self_person_relationship",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_person.full_name} -> {self.target_person.full_name}"


class PortalPasswordResetToken(TimeStampedModel):
    access_account = models.ForeignKey(
        PortalAccount,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=64, unique=True, default="")
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Reset token for {self.access_account.person.full_name}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid4().hex
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=2)
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        return self.used_at is None and timezone.now() <= self.expires_at

    def mark_as_used(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=("used_at", "updated_at"))
