from django.core.management.base import BaseCommand

from system.services.test_seed_fixtures import seed_test_people_fixture


DATA_FILENAME = "seed_system_initial_test_teachers.json"


class Command(BaseCommand):
    help = f"Carrega professores ficticios de homologacao a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_test_teachers"))
        summary = seed_test_people_fixture(DATA_FILENAME)
        self.stdout.write(
            self.style.SUCCESS(
                "\nHomologacao professores: "
                f"{summary['people_created']} criado(s), "
                f"{summary['people_updated']} atualizado(s), "
                f"{summary['portal_accounts']} conta(s), "
                f"{summary['instructor_assignments']} apoio(s) de turma, "
                f"{summary['relationships']} relacionamento(s)."
            )
        )
