import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models.graduation import BeltRank


DATA_FILENAME = "seed_system_initial_belt_ranks.json"


class Command(BaseCommand):
    help = f"Cria as faixas iniciais a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_belt_ranks"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhuma faixa encontrada no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            # Primeira passagem: cria/atualiza todas as faixas sem next_rank
            belt_map = {}
            for entry in data:
                code = entry.get("code", "").strip()
                if not code:
                    raise CommandError(f"Entrada inválida no JSON: 'code' é obrigatório. Entrada: {entry}")

                belt, created = BeltRank.objects.get_or_create(
                    code=code,
                    defaults=self._build_defaults(entry),
                )
                if not created:
                    self._apply_updates(belt, entry)
                    belt.save()

                belt_map[code] = belt
                status = "criado" if created else "atualizado"
                self.stdout.write(f"  [{status}] {belt.display_name} (code={code})")
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            # Segunda passagem: vincula next_rank agora que todas as faixas existem
            for entry in data:
                next_code = entry.get("next_code")
                if not next_code:
                    continue
                belt = belt_map[entry["code"]]
                next_belt = belt_map.get(next_code)
                if next_belt is None:
                    raise CommandError(
                        f"Faixa de destino '{next_code}' referenciada em '{entry['code']}' não encontrada no JSON."
                    )
                if belt.next_rank_id != next_belt.pk:
                    belt.next_rank = next_belt
                    belt.save(update_fields=["next_rank"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\nFaixas: {created_count} criada(s), {updated_count} atualizada(s)."
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
            "color_hex": entry.get("color_hex", "#000000"),
            "tip_color_hex": entry.get("tip_color_hex", "#000000"),
            "stripe_color_hex": entry.get("stripe_color_hex", "#ffffff"),
            "max_grades": entry.get("max_grades", 4),
            "min_age": entry.get("min_age"),
            "max_age": entry.get("max_age"),
            "display_order": entry.get("display_order", 0),
        }

    def _apply_updates(self, belt: BeltRank, entry: dict) -> None:
        belt.display_name = entry["display_name"]
        belt.audience = entry["audience"]
        belt.color_hex = entry.get("color_hex", "#000000")
        belt.tip_color_hex = entry.get("tip_color_hex", "#000000")
        belt.stripe_color_hex = entry.get("stripe_color_hex", "#ffffff")
        belt.max_grades = entry.get("max_grades", 4)
        belt.min_age = entry.get("min_age")
        belt.max_age = entry.get("max_age")
        belt.display_order = entry.get("display_order", 0)
