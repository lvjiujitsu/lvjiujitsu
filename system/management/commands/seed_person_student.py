from django.core.management.base import BaseCommand

from system.services.seeding import DEFAULT_TEST_PORTAL_PASSWORD, seed_person_student


class Command(BaseCommand):
    help = "Cria ou atualiza a seed de aluno individual."

    def handle(self, *args, **options):
        created = seed_person_student(password=DEFAULT_TEST_PORTAL_PASSWORD)
        self.stdout.write(
            self.style.SUCCESS(
                f"Aluno individual processado: {created['student'].full_name} ({created['student'].cpf})"
            )
        )
