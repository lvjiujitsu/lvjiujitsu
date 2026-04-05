from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Executa as seeds base e cenarios simples de validacao manual do portal."

    def handle(self, *args, **options):
        call_command("inicial_seed", stdout=self.stdout)
        call_command("seed_person_student", stdout=self.stdout)
        call_command("seed_person_student_with_dependent", stdout=self.stdout)
        call_command("seed_person_guardian", stdout=self.stdout)
        call_command("seed_person_guardian_with_dependent", stdout=self.stdout)
        call_command("seed_person_administrative", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Seed inicial de teste concluida com sucesso."))
