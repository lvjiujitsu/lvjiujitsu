from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


_DEBUG_SEED_COMMANDS = [
    "create_admin_superuser",
    "seed_system_initial_person_type",
    "seed_system_initial_belt_ranks",
    "seed_system_initial_teacher",
    "seed_system_initial_administrative",
    "seed_system_initial_class_categories",
    "seed_system_initial_class_categories_teacher",
    "seed_system_initial_class_categories_administrative",
    "seed_system_initial_class_catalog",
    "seed_system_initial_teacher_payroll_configs",
    "seed_system_initial_class_catalog_administrative",
    "seed_system_initial_holidays",
    "seed_system_initial_ibjjf_age_categories",
    "seed_system_initial_graduation_rules",
    "seed_system_initial_product_categories",
    "seed_system_initial_product_catalog",
    "seed_system_initial_subscription_plans",
    "seed_system_initial_subscription_plans_values",
    "seed_system_initial_subscription_plans_stripe",
    "seed_system_initial_coupons",
]


class Command(BaseCommand):
    help = (
        "Bootstrap do ambiente: migrate sempre; seeds completas apenas quando DEBUG=True."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== bootstrap: migrate ==="))
        call_command("migrate", "--noinput", verbosity=1)
        self.stdout.write(self.style.SUCCESS("migrate concluido."))

        if not settings.DEBUG:
            self.stdout.write(
                self.style.SUCCESS(
                    "Ambiente de producao (DEBUG=False) — seeds ignoradas."
                )
            )
            return

        self.stdout.write(
            self.style.MIGRATE_HEADING("=== bootstrap: seeds (DEBUG=True) ===")
        )
        for command in _DEBUG_SEED_COMMANDS:
            self.stdout.write(f"  -> {command}")
            try:
                call_command(command, verbosity=1)
            except Exception as exc:
                self.stdout.write(
                    self.style.WARNING(f"     AVISO: '{command}' falhou — {exc}")
                )

        self.stdout.write(self.style.SUCCESS("=== bootstrap concluido ==="))
