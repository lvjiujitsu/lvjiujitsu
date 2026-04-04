from django.core.management.base import BaseCommand

from system.services.seeding import DEFAULT_TEST_PORTAL_PASSWORD, seed_person_guardian


class Command(BaseCommand):
    help = "Cria ou atualiza a seed de responsavel sem dependente."

    def handle(self, *args, **options):
        created = seed_person_guardian(password=DEFAULT_TEST_PORTAL_PASSWORD)
        self.stdout.write(
            self.style.SUCCESS(
                f"Responsavel individual processado: {created['guardian'].full_name} ({created['guardian'].cpf})"
            )
        )
