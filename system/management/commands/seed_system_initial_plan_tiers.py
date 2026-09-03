import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models.plan import PlanTier


DATA_FILENAME = "seed_system_initial_plan_tiers.json"


class Command(BaseCommand):
    help = f"Cria os tiers comerciais (audience x frequência) a partir de static/business_rule/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_plan_tiers"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhum tier encontrado no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                code = entry.get("code", "").strip()
                if not code:
                    raise CommandError(f"Entrada inválida no JSON: 'code' é obrigatório. Entrada: {entry}")

                tier, created = PlanTier.objects.update_or_create(
                    code=code,
                    defaults=self._build_defaults(entry),
                )
                status = "criado" if created else "atualizado"
                self.stdout.write(
                    f"  [{status}] {tier.display_name} "
                    f"(code={code}, desconto família={tier.family_discount_percentage * 100}%)"
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTiers comerciais: {created_count} criado(s), {updated_count} atualizado(s)."
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
            "audience": entry.get("audience", "adult"),
            "weekly_frequency": entry["weekly_frequency"],
            "family_discount_percentage": (
                Decimal(str(entry.get("family_discount_percentage", "0"))) / Decimal("100")
            ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "display_order": entry.get("display_order", 0),
            "is_active": entry.get("is_active", True),
        }
