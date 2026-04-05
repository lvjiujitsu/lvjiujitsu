from django.core.management.base import BaseCommand

from system.services.seeding import DEFAULT_TEST_PORTAL_PASSWORD, seed_person_administrative


class Command(BaseCommand):
    help = "Cria ou atualiza a seed de pessoa administrativa."

    def handle(self, *args, **options):
        created = seed_person_administrative(password=DEFAULT_TEST_PORTAL_PASSWORD)
        self.stdout.write(
            self.style.SUCCESS(
                "Administrativo processado: "
                f"{created['administrative'].full_name} ({created['administrative'].cpf})"
            )
        )
