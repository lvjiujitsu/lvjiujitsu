import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_date

from system.models import Holiday


DATA_FILENAME = "seed_system_initial_holidays.json"


class Command(BaseCommand):
    help = f"Cria feriados iniciais a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_holidays"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhum feriado encontrado no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                date = self._get_required_date(entry)
                name = self._get_required_value(entry, "name")

                holiday, created = Holiday.objects.update_or_create(
                    date=date,
                    defaults={
                        "name": name,
                        "is_active": entry.get("is_active", True),
                    },
                )

                status = "criado" if created else "atualizado"
                self.stdout.write(f"  [{status}] {holiday.date:%d/%m/%Y} - {holiday.name}")

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nFeriados: {created_count} criado(s), {updated_count} atualizado(s)."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo nao encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_required_value(self, entry: dict, field_name: str) -> str:
        value = entry.get(field_name, "")
        if not isinstance(value, str) or not value.strip():
            raise CommandError(f"Entrada invalida no JSON: '{field_name}' e obrigatorio. Entrada: {entry}")
        return value.strip()

    def _get_required_date(self, entry: dict):
        raw_date = self._get_required_value(entry, "date")
        parsed_date = parse_date(raw_date)
        if parsed_date is None:
            raise CommandError(f"Entrada invalida no JSON: 'date' deve estar em YYYY-MM-DD. Entrada: {entry}")
        return parsed_date
