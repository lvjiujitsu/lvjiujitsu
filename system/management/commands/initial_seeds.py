from django.core.management.base import BaseCommand

from system.services.seeds import run_initial_seed_pipeline


class Command(BaseCommand):
    help = "Carrega os seeds iniciais do projeto LV JIU JITSU com dados publicos e catalogos operacionais."

    def handle(self, *args, **options):
        message = run_initial_seed_pipeline(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(message))
