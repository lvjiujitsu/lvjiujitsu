from django.core.management.base import BaseCommand

from system.services.seeding import seed_plans


class Command(BaseCommand):
    help = "Seed subscription plans from SumUp store data."

    def handle(self, *args, **options):
        result = seed_plans()
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(result)} plans."))
