from django.core.management.base import BaseCommand

from system.services.seeding import DEFAULT_TEST_PORTAL_PASSWORD, seed_class_matrix


class Command(BaseCommand):
    help = "Cria a matriz N:N entre auxiliares administrativos, alunos elegíveis e turmas."

    def handle(self, *args, **options):
        result = seed_class_matrix()

        self.stdout.write("Matriz N:N de turmas criada com sucesso.")
        self.stdout.write(
            f"Senha padrão de login para as contas de teste: {DEFAULT_TEST_PORTAL_PASSWORD}"
        )
        self.stdout.write(f"- Turmas base: {len(result['catalog']['class_groups'])}")
        self.stdout.write(
            f"- Vínculos N:N de instrutores auxiliares: {len(result['instructor_assignments'])}"
        )
        self.stdout.write(
            f"- Matrículas N:N de alunos/dependentes: {len(result['enrollments'])}"
        )
        self.stdout.write(self.style.SUCCESS("Seed de matriz de turmas concluída com sucesso."))
