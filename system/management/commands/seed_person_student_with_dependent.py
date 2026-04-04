from django.core.management.base import BaseCommand

from system.services.seeding import (
    DEFAULT_TEST_PORTAL_PASSWORD,
    seed_person_student_with_dependent,
)


class Command(BaseCommand):
    help = "Cria ou atualiza a seed de aluno titular com dependente."

    def handle(self, *args, **options):
        created = seed_person_student_with_dependent(password=DEFAULT_TEST_PORTAL_PASSWORD)
        self.stdout.write(
            self.style.SUCCESS(
                "Aluno titular com dependente processado: "
                f"{created['holder'].full_name} -> {created['dependent'].full_name}"
            )
        )
