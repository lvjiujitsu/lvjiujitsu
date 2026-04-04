from django.core.management.base import BaseCommand

from system.services.seeding import seed_class_catalog


class Command(BaseCommand):
    help = "Cria o catálogo base de turmas, categorias e horários do sistema."

    def handle(self, *args, **options):
        result = seed_class_catalog()

        self.stdout.write("Catálogo base de turmas criado com sucesso.")
        self.stdout.write(f"- Turmas: {len(result['class_groups'])}")
        self.stdout.write(
            f"- Professores principais com acesso de portal: {len(result['teachers'])}"
        )
        self.stdout.write(self.style.SUCCESS("Seed de catálogo de turmas concluída com sucesso."))
