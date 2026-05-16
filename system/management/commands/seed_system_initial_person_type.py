from django.core.management.base import BaseCommand

from system.constants import DEFAULT_PERSON_TYPE_DEFINITIONS
from system.models import PersonType


class Command(BaseCommand):
    help = "Cria os tipos de pessoa base definidos em system/constants.py."

    def handle(self, *args, **options):
        created_count = 0
        for code, attrs in DEFAULT_PERSON_TYPE_DEFINITIONS.items():
            _, created = PersonType.objects.get_or_create(
                code=code,
                defaults={
                    "display_name": attrs["display_name"],
                    "description": attrs["description"],
                },
            )
            status = "criado" if created else "já existe"
            self.stdout.write(f"  [{status}] {attrs['display_name']} (code={code})")
            if created:
                created_count += 1

        total = len(DEFAULT_PERSON_TYPE_DEFINITIONS)
        self.stdout.write(
            self.style.SUCCESS(
                f"\nTipos de pessoa: {created_count} criado(s), {total - created_count} já existia(m)."
            )
        )
