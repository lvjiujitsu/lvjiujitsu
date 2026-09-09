from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from system.core.mail import EmailDeliveryError, check_brevo_account


class Command(BaseCommand):
    help = (
        "Valida o canal de e-mail configurado sem enviar mensagem nem exibir "
        "credencial."
    )

    def handle(self, *args, **options):
        backend = settings.EMAIL_BACKEND
        self.stdout.write(f"Backend configurado: {backend}")
        self.stdout.write(f"Timeout de entrega: {settings.EMAIL_TIMEOUT}s")
        self.stdout.write(
            "Remetente: "
            + ("definido" if settings.DEFAULT_FROM_EMAIL else "ausente")
        )

        if not backend.endswith("BrevoEmailBackend"):
            self.stdout.write(
                self.style.WARNING(
                    "O canal não usa a Brevo; nada a validar remotamente."
                )
            )
            return

        try:
            scope = check_brevo_account()
        except EmailDeliveryError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(f"Credencial da Brevo: {scope}.")
        )
