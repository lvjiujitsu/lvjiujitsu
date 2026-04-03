import secrets
from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone as django_timezone

from system.constants import PASSWORD_ACTION_FIRST_ACCESS, PASSWORD_ACTION_RESET
from system.models.base import BaseModel
from system.services.auth.cpf import normalize_cpf


class SystemUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, cpf, password, **extra_fields):
        normalized_cpf = normalize_cpf(cpf)
        if not normalized_cpf:
            raise ValueError("CPF is required")
        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)
        user = self.model(cpf=normalized_cpf, **extra_fields)
        if password:
            user.set_password(password)
            user.must_change_password = False
        else:
            user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, cpf, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(cpf, password, **extra_fields)

    def create_superuser(self, cpf, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("must_change_password", False)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(cpf, password, **extra_fields)


class SystemRole(BaseModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.code


class SystemUser(BaseModel, AbstractBaseUser, PermissionsMixin):
    cpf = models.CharField(max_length=11, unique=True, db_index=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    full_name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=django_timezone.now)
    roles = models.ManyToManyField(SystemRole, through="SystemUserRole", related_name="users")

    objects = SystemUserManager()

    USERNAME_FIELD = "cpf"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ("full_name", "cpf")

    def clean(self):
        super().clean()
        self.cpf = normalize_cpf(self.cpf)
        if not self.cpf:
            raise ValidationError({"cpf": "CPF invalido."})
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
        else:
            self.email = None

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.cpf})"

    def assign_role(self, role):
        SystemUserRole.objects.get_or_create(user=self, role=role)

    def has_role(self, role_code):
        return self.roles.filter(code=role_code).exists()

    def has_any_role(self, *role_codes):
        if self.is_superuser:
            return True
        if not role_codes:
            return False
        return self.roles.filter(code__in=role_codes).exists()


class SystemUserRole(BaseModel):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name="role_links")
    role = models.ForeignKey(SystemRole, on_delete=models.CASCADE, related_name="user_links")

    class Meta:
        unique_together = ("user", "role")
        ordering = ("user", "role")

    def __str__(self):
        return f"{self.user_id}:{self.role.code}"


class AuthenticationEvent(BaseModel):
    EVENT_LOGIN_SUCCESS = "login_success"
    EVENT_LOGIN_FAILURE = "login_failure"
    EVENT_LOGOUT = "logout"
    EVENT_PASSWORD_RESET_REQUEST = "password_reset_request"
    EVENT_PASSWORD_RESET_SUCCESS = "password_reset_success"
    EVENT_FIRST_ACCESS_REQUEST = "first_access_request"
    EVENT_FIRST_ACCESS_SUCCESS = "first_access_success"
    EVENT_PROFILE_UPDATE = "profile_update"
    EVENT_PASSWORD_CHANGE = "password_change"

    EVENT_CHOICES = (
        (EVENT_LOGIN_SUCCESS, "Login Success"),
        (EVENT_LOGIN_FAILURE, "Login Failure"),
        (EVENT_LOGOUT, "Logout"),
        (EVENT_PASSWORD_RESET_REQUEST, "Password Reset Request"),
        (EVENT_PASSWORD_RESET_SUCCESS, "Password Reset Success"),
        (EVENT_FIRST_ACCESS_REQUEST, "First Access Request"),
        (EVENT_FIRST_ACCESS_SUCCESS, "First Access Success"),
        (EVENT_PROFILE_UPDATE, "Profile Update"),
        (EVENT_PASSWORD_CHANGE, "Password Change"),
    )

    actor_user = models.ForeignKey(
        SystemUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authentication_events",
    )
    identifier = models.CharField(max_length=64, blank=True)
    event_type = models.CharField(max_length=64, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)


class PasswordActionToken(BaseModel):
    PURPOSE_CHOICES = (
        (PASSWORD_ACTION_FIRST_ACCESS, "First Access"),
        (PASSWORD_ACTION_RESET, "Password Reset"),
    )

    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name="password_action_tokens")
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES)
    token = models.CharField(max_length=96, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    @classmethod
    def issue(cls, user, purpose, ttl_minutes=60):
        return cls.objects.create(
            user=user,
            purpose=purpose,
            token=secrets.token_urlsafe(32),
            expires_at=django_timezone.now() + timedelta(minutes=ttl_minutes),
        )

    @property
    def is_expired(self):
        return django_timezone.now() >= self.expires_at

    @property
    def is_usable(self):
        return self.used_at is None and not self.is_expired

    def mark_used(self):
        self.used_at = django_timezone.now()
        self.save(update_fields=["used_at", "updated_at"])
