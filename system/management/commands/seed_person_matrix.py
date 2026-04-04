from django.core.management.base import BaseCommand

from system.services.seeding import DEFAULT_TEST_PORTAL_PASSWORD, seed_person_matrix


class Command(BaseCommand):
    help = "Cria uma matriz completa com todas as combinacoes N:N de tipos de pessoa."

    def handle(self, *args, **options):
        result = seed_person_matrix()
        matrix_people = result["matrix_people"]

        self.stdout.write("Matriz N:N de tipos criada com sucesso.")
        self.stdout.write(
            f"Senha padrao de login para todas as contas de teste: {DEFAULT_TEST_PORTAL_PASSWORD}"
        )

        for entry in matrix_people:
            person = entry["person"]
            type_codes = ", ".join(entry["type_codes"])
            self.stdout.write(
                f"- {entry['index']:02d} | {person.full_name} | {person.cpf} | {type_codes}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed de matriz concluida com sucesso. Total de combinacoes: {len(matrix_people)}."
            )
        )
