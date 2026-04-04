from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Executa as seeds base e a matriz completa N:N de teste do portal."

    def handle(self, *args, **options):
        call_command("inicial_seed", stdout=self.stdout)
        call_command("seed_person_matrix", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Seed inicial de teste concluida com sucesso."))
