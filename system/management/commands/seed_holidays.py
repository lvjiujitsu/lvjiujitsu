from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from system.models.calendar import Holiday


NATIONAL_HOLIDAYS_2026 = (
    (date(2026, 1, 1), "Confraternização Universal"),
    (date(2026, 2, 16), "Carnaval"),
    (date(2026, 2, 17), "Carnaval"),
    (date(2026, 4, 3), "Sexta-feira Santa"),
    (date(2026, 4, 21), "Tiradentes"),
    (date(2026, 5, 1), "Dia do Trabalho"),
    (date(2026, 6, 4), "Corpus Christi"),
    (date(2026, 9, 7), "Independência do Brasil"),
    (date(2026, 10, 12), "Nossa Senhora Aparecida"),
    (date(2026, 11, 2), "Finados"),
    (date(2026, 11, 15), "Proclamação da República"),
    (date(2026, 12, 25), "Natal"),
)


class Command(BaseCommand):
    help = "Seed national holidays for 2026."

    @transaction.atomic
    def handle(self, *args, **options):
        count = 0
        for holiday_date, name in NATIONAL_HOLIDAYS_2026:
            _, created = Holiday.objects.update_or_create(
                date=holiday_date,
                defaults={"name": name, "is_active": True},
            )
            if created:
                count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {count} new holidays ({len(NATIONAL_HOLIDAYS_2026)} total).")
        )
