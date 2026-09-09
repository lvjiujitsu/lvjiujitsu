from django.core.management.base import BaseCommand

from system.business_rule.services.seed_test_fixtures import seed_test_people_fixture


DATA_FILENAME = "seed_system_initial_test_students.json"


class Command(BaseCommand):
    help = f"Carrega alunos ficticios de homologacao a partir de static/business_rule/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_test_students"))
        summary = seed_test_people_fixture(DATA_FILENAME)
        self.stdout.write(
            self.style.SUCCESS(
                "\nHomologacao alunos: "
                f"{summary['people_created']} criado(s), "
                f"{summary['people_updated']} atualizado(s), "
                f"{summary['portal_accounts']} conta(s), "
                f"{summary['relationships']} relacionamento(s)."
            )
        )
