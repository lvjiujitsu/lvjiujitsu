from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Executa as seeds base do sistema."

    def handle(self, *args, **options):
        call_command("seed_person_type", stdout=self.stdout)
        call_command("seed_class_catalog", stdout=self.stdout)
        call_command("seed_products", stdout=self.stdout)
        call_command("seed_plans", stdout=self.stdout)
        call_command("seed_holidays", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Seed inicial concluida com sucesso."))
