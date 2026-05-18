import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import IbjjfAgeCategory


DATA_FILENAME = "seed_system_initial_ibjjf_age_categories.json"


class Command(BaseCommand):
    help = f"Cria as categorias de idade IBJJF a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_ibjjf_age_categories"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhuma categoria encontrada no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                code = entry.get("code", "").strip()
                if not code:
                    raise CommandError(f"Entrada inválida no JSON: 'code' é obrigatório. Entrada: {entry}")

                category, created = IbjjfAgeCategory.objects.get_or_create(
                    code=code,
                    defaults=self._build_defaults(entry),
                )
                if not created:
                    self._apply_updates(category, entry)
                    category.save()

                status = "criado" if created else "atualizado"
                self.stdout.write(f"  [{status}] {category.display_name} (code={code})")
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCategorias IBJJF: {created_count} criada(s), {updated_count} atualizada(s)."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _build_defaults(self, entry: dict) -> dict:
        return {
            "display_name": entry["display_name"],
            "audience": entry["audience"],
            "minimum_age": entry["minimum_age"],
            "maximum_age": entry.get("maximum_age"),
            "display_order": entry.get("display_order", 0),
        }

    def _apply_updates(self, category: IbjjfAgeCategory, entry: dict) -> None:
        category.display_name = entry["display_name"]
        category.audience = entry["audience"]
        category.minimum_age = entry["minimum_age"]
        category.maximum_age = entry.get("maximum_age")
        category.display_order = entry.get("display_order", 0)
