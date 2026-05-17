import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import BeltRank, GraduationRule


class Command(BaseCommand):
    help = "Cria as regras de graduação a partir de static/initial_data/graduation_rules.json."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_graduation_rules"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING("Nenhuma regra encontrada no arquivo graduation_rules.json."))
            return

        self._check_belt_ranks_exist()

        belt_map = {b.code: b for b in BeltRank.objects.all()}

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                belt_code = entry.get("belt_code", "").strip()
                if not belt_code:
                    raise CommandError(f"Entrada inválida no JSON: 'belt_code' é obrigatório. Entrada: {entry}")

                belt = belt_map.get(belt_code)
                if belt is None:
                    raise CommandError(
                        f"Faixa '{belt_code}' não encontrada. "
                        f"Execute seed_system_initial_belt_ranks antes desta seed."
                    )

                from_grade = entry["from_grade"]
                rule, created = GraduationRule.objects.get_or_create(
                    belt_rank=belt,
                    from_grade=from_grade,
                    defaults=self._build_defaults(entry),
                )
                if not created:
                    self._apply_updates(rule, entry)
                    rule.save()

                to_label = f"grau {rule.to_grade}" if rule.to_grade is not None else "próxima faixa"
                status = "criada" if created else "atualizada"
                self.stdout.write(
                    f"  [{status}] {belt.display_name} grau {from_grade} → {to_label}"
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nRegras de graduação: {created_count} criada(s), {updated_count} atualizada(s)."
            )
        )

    def _check_belt_ranks_exist(self) -> None:
        if not BeltRank.objects.exists():
            raise CommandError(
                "Nenhuma faixa encontrada no banco. "
                "Execute seed_system_initial_belt_ranks antes desta seed."
            )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / "graduation_rules.json"
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _build_defaults(self, entry: dict) -> dict:
        return {
            "to_grade": entry.get("to_grade"),
            "min_months_in_current_grade": entry["min_months"],
            "min_classes_required": entry["min_classes"],
            "min_classes_window_months": entry["window_months"],
        }

    def _apply_updates(self, rule: GraduationRule, entry: dict) -> None:
        rule.to_grade = entry.get("to_grade")
        rule.min_months_in_current_grade = entry["min_months"]
        rule.min_classes_required = entry["min_classes"]
        rule.min_classes_window_months = entry["window_months"]
