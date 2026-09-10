from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

PRODUCTION_ENVIRONMENT = "prod"


class DestructiveCommand(BaseCommand):
    confirmation_token = ""

    def add_arguments(self, parser):
        parser.add_argument("--confirm", required=True)
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Confirma a execução destrutiva em produção.",
        )

    def guard(self, options):
        if options["confirm"] != self.confirmation_token:
            raise CommandError(
                f"Confirmação inválida. Use --confirm {self.confirmation_token}."
            )
        environment = getattr(settings, "DJANGO_ENVIRONMENT", "")
        if environment == PRODUCTION_ENVIRONMENT and not options["allow_production"]:
            raise CommandError(
                "Produção recusada. Repita com --allow-production para confirmar."
            )
