from django.core.management.base import BaseCommand

from system.services.seeding import seed_person_types


class Command(BaseCommand):
    help = "Cria ou atualiza os tipos base de pessoa do portal."

    def handle(self, *args, **options):
        person_types = seed_person_types()
        self.stdout.write(self.style.SUCCESS("Tipos de pessoa processados com sucesso."))
        for code, person_type in person_types.items():
            self.stdout.write(f"- {code}: {person_type.display_name}")
