from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cria ou atualiza o superusuário a partir de ADMIN_SUPERUSER_*."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-if-unconfigured",
            action="store_true",
            help="Não falha quando e-mail ou senha não estiverem configurados.",
        )

    def handle(self, *args, **options):
        username = settings.ADMIN_SUPERUSER_USERNAME.strip() or "admin"
        email = settings.ADMIN_SUPERUSER_EMAIL.strip()
        password = settings.ADMIN_SUPERUSER_PASSWORD

        if not email or not password:
            if options["skip_if_unconfigured"]:
                self.stdout.write(
                    self.style.WARNING(
                        "Superusuário não configurado; defina ADMIN_SUPERUSER_EMAIL e "
                        "ADMIN_SUPERUSER_PASSWORD."
                    )
                )
                return
            raise CommandError(
                "ADMIN_SUPERUSER_EMAIL e ADMIN_SUPERUSER_PASSWORD são obrigatórios."
            )

        user, created = get_user_model().objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Superusuário '{username}' {action}."))

