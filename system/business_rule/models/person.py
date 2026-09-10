
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from system.core.models import TimeStampedModel
from system.business_rule.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES, PersonTypeCode


class PersonType(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    display_name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_name",)

    def __str__(self) -> str:
        return self.display_name


class OperationalRole(TimeStampedModel):
    code = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    capabilities = models.JSONField(default=list, blank=True)
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


class MartialArt(models.TextChoices):
    JIU_JITSU = "jiu_jitsu", "Jiu Jitsu"
    MUAY_THAI = "muay_thai", "Muay Thai"
    JUDO = "judo", "Judô"
    KARATE = "karate", "Karatê"
    BOXING = "boxing", "Boxe"
    WRESTLING = "wrestling", "Wrestling"
    OTHER = "other", "Outra"


class JiuJitsuBelt(models.TextChoices):
    WHITE = "white", "Branca"
    BLUE = "blue", "Azul"
    PURPLE = "purple", "Roxa"
    BROWN = "brown", "Marrom"
    BLACK = "black", "Preta"
    RED_BLACK = "red_black", "Vermelha e Preta"
    RED_WHITE = "red_white", "Vermelha e Branca"
    RED = "red", "Vermelha"


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
    martial_art = models.CharField(max_length=24, choices=MartialArt.choices, blank=True)
    martial_art_graduation = models.CharField(max_length=120, blank=True)
    jiu_jitsu_belt = models.CharField(max_length=24, choices=JiuJitsuBelt.choices, blank=True)
    jiu_jitsu_stripes = models.PositiveSmallIntegerField(null=True, blank=True)
    martial_art_started_at = models.DateField(
        "Início no jiu jitsu",
        null=True,
        blank=True,
        help_text="Data aproximada em que começou a praticar jiu jitsu, em qualquer academia.",
    )
    martial_art_last_graduation_at = models.DateField(
        "Última graduação anterior",
        null=True,
        blank=True,
        help_text="Data da última graduação recebida antes de entrar na LV.",
    )
    previous_academy = models.CharField(
        "Academia anterior",
        max_length=200,
        blank=True,
        default="",
    )
    person_type = models.ForeignKey(
        PersonType,
        on_delete=models.PROTECT,
        related_name="people",
        null=True,
        blank=True,
    )
    class_category = models.ForeignKey(
        "business_rule.ClassCategory",
        on_delete=models.SET_NULL,
        related_name="people",
        null=True,
        blank=True,
    )
    class_group = models.ForeignKey(
        "business_rule.ClassGroup",
        on_delete=models.SET_NULL,
        related_name="people",
        null=True,
        blank=True,
    )
    class_schedule = models.ForeignKey(
        "business_rule.ClassSchedule",
        on_delete=models.SET_NULL,
        related_name="people",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    stripe_customer_id = models.CharField(
        "ID do cliente Stripe",
        max_length=120,
        blank=True,
        default="",
    )
    asaas_customer_id = models.CharField(
        "ID do cliente Asaas",
        max_length=120,
        blank=True,
        default="",
    )
    postal_code = models.CharField("CEP", max_length=9, blank=True, default="")
    address = models.CharField("Logradouro", max_length=255, blank=True, default="")
    address_number = models.CharField("Número", max_length=20, blank=True, default="")
    address_complement = models.CharField("Complemento", max_length=100, blank=True, default="")
    address_neighborhood = models.CharField("Bairro", max_length=100, blank=True, default="")
    city = models.CharField("Cidade", max_length=100, blank=True, default="")
    veteran_plan_approved = models.BooleanField(
        "Plano Veterano aprovado manualmente",
        default=False,
    )
    veteran_plan_approved_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="veteran_plan_approvals_made",
        null=True,
        blank=True,
        verbose_name="Aprovado por",
    )
    veteran_plan_approved_at = models.DateTimeField(
        "Aprovado em",
        null=True,
        blank=True,
    )
    veteran_plan_approved_notes = models.TextField(
        "Justificativa da aprovação",
        blank=True,
        default="",
    )

    class Meta:
        ordering = ("full_name",)

    def __str__(self) -> str:
        return self.full_name

    def has_type_code(self, *codes: str) -> bool:
        if not self.person_type_id:
            return False
        return self.person_type.code in codes

    def has_operational_role(self, *codes: str) -> bool:
        from system.business_rule.services.portal_capabilities import (
            get_person_operational_role_codes,
        )

        return bool(set(codes) & get_person_operational_role_codes(self))

    def has_capability(self, *capabilities: str) -> bool:
        from system.business_rule.services.portal_capabilities import (
            person_has_any_capability,
        )

        return person_has_any_capability(self, *capabilities)

    def can_enroll_in_class_group(self) -> bool:

        if self.has_type_code(*CLASS_ENROLLMENT_PERSON_TYPE_CODES):
            return True
        return self.has_type_code(PersonTypeCode.ADMINISTRATIVE_ASSISTANT) and bool(
            self.jiu_jitsu_belt or self.class_enrollments.filter(status="active").exists()
        )

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

class PersonOperationalRole(TimeStampedModel):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="operational_role_assignments",
    )
    role = models.ForeignKey(
        OperationalRole,
        on_delete=models.PROTECT,
        related_name="person_assignments",
    )
    class_group = models.ForeignKey(
        "business_rule.ClassGroup",
        on_delete=models.CASCADE,
        related_name="operational_role_assignments",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("person__full_name", "role__display_name")
        constraints = [
            models.UniqueConstraint(
                fields=("person", "role"),
                condition=Q(class_group__isnull=True),
                name="unique_person_global_operational_role",
            ),
            models.UniqueConstraint(
                fields=("person", "role", "class_group"),
                name="unique_person_scoped_operational_role",
            ),
        ]

    def __str__(self) -> str:
        scope = f" / {self.class_group}" if self.class_group_id else ""
        return f"{self.person.full_name} -> {self.role.display_name}{scope}"


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
        indexes = [
            models.Index(
                fields=["source_person", "relationship_kind"],
                name="personrel_source_kind_idx",
            ),
            models.Index(
                fields=["target_person", "relationship_kind"],
                name="personrel_target_kind_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("source_person", "target_person", "relationship_kind"),
                name="unique_person_relationship",
            ),
            models.CheckConstraint(
                condition=~Q(source_person=F("target_person")),
                name="prevent_self_person_relationship",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_person.full_name} -> {self.target_person.full_name}"
