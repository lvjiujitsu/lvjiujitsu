from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Cria ou atualiza o superusuario administrativo a partir das variaveis do .env."

    def handle(self, *args, **options):
        username = self._get_setting("ADMIN_SUPERUSER_USERNAME")
        email = self._get_setting("ADMIN_SUPERUSER_EMAIL")
        password = self._get_setting("ADMIN_SUPERUSER_PASSWORD")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "criado" if created else "atualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Superusuario administrativo '{username}' {action} com sucesso."
            )
        )

    def _get_setting(self, key: str) -> str:
        value = getattr(settings, key, "").strip()
        if not value:
            raise CommandError(
                f"A configuracao '{key}' nao foi definida no arquivo .env."
            )
        return value
