from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from system.models.calendar import Holiday


FIXED_NATIONAL_HOLIDAYS = (
    (1, 1, "Confraternização Universal"),
    (4, 21, "Tiradentes"),
    (5, 1, "Dia Mundial do Trabalho"),
    (9, 7, "Independência do Brasil"),
    (10, 12, "Nossa Senhora Aparecida"),
    (11, 2, "Finados"),
    (11, 15, "Proclamação da República"),
    (11, 20, "Dia Nacional de Zumbi e da Consciência Negra"),
    (12, 25, "Natal"),
)


class Command(BaseCommand):
    help = "Seed Brazilian calendar closure dates for a configurable year."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=timezone.localdate().year,
            help="Year to seed. Defaults to the current local year.",
        )
        parser.add_argument(
            "--without-optional",
            action="store_true",
            help="Do not seed common optional closure dates such as Carnival and Corpus Christi.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        year = options["year"]
        include_optional = not options["without_optional"]
        closure_dates = get_brazilian_closure_dates(year, include_optional=include_optional)

        created_count = 0
        for holiday_date, name in closure_dates:
            _, created = Holiday.objects.update_or_create(
                date=holiday_date,
                defaults={"name": name, "is_active": True},
            )
            if created:
                created_count += 1

        self.stdout.write(f"Feriados cadastrados para {year}: {len(closure_dates)}")
        for holiday_date, name in closure_dates:
            self.stdout.write(f"- {holiday_date.isoformat()}: {name}")
        self.stdout.write(
            self.style.SUCCESS(f"Seed de feriados concluída: {created_count} novos.")
        )


def get_brazilian_closure_dates(year, *, include_optional=True):
    easter = calculate_easter_date(year)
    holidays = [
        (date(year, month, day), name)
        for month, day, name in FIXED_NATIONAL_HOLIDAYS
    ]
    holidays.append((easter - timedelta(days=2), "Paixão de Cristo"))

    if include_optional:
        holidays.extend(
            (
                (easter - timedelta(days=48), "Carnaval"),
                (easter - timedelta(days=47), "Carnaval"),
                (easter + timedelta(days=60), "Corpus Christi"),
            )
        )

    return sorted(holidays, key=lambda item: item[0])


def calculate_easter_date(year):
    century = year // 100
    year_remainder = year % 100
    golden_number = year % 19
    leap_correction = century // 4
    century_remainder = century % 4
    epact_adjustment = (century + 8) // 25
    moon_correction = (century - epact_adjustment + 1) // 3
    epact = (
        19 * golden_number
        + century
        - leap_correction
        - moon_correction
        + 15
    ) % 30
    weekday_correction = (
        32
        + 2 * century_remainder
        + 2 * (year_remainder // 4)
        - epact
        - year_remainder % 4
    ) % 7
    month_offset = (golden_number + 11 * epact + 22 * weekday_correction) // 451
    month = (epact + weekday_correction - 7 * month_offset + 114) // 31
    day = ((epact + weekday_correction - 7 * month_offset + 114) % 31) + 1
    return date(year, month, day)
