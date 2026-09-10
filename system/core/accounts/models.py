from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from system.core.models import TimeStampedModel


class TechnicalUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra):
        username = (username or "").strip()
        if not username:
            raise ValueError("O usuário precisa de um nome de acesso.")
        user = self.model(username=username, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email="", password=None, **extra):
        extra.update({"is_staff": True, "is_superuser": True})
        return self.create_user(username, password=password, email=email, **extra)


class AbstractTechnicalUser(AbstractBaseUser, TimeStampedModel):
    username = models.CharField("usuário", max_length=150, unique=True)
    name = models.CharField("nome", max_length=150, blank=True)
    email = models.EmailField("e-mail", max_length=254, blank=True)
    is_active = models.BooleanField("conta ativa", default=True)
    is_staff = models.BooleanField(
        "acessa o Django Admin técnico",
        default=False,
        help_text="Só governa /django-admin/; quem opera o produto é o perfil.",
    )
    is_superuser = models.BooleanField("superusuário", default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = TechnicalUserManager()

    class Meta:
        abstract = True
        ordering = ("username",)
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.name or self.username

    def get_short_name(self):
        return self.name.split(" ")[0] if self.name else self.username

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser
