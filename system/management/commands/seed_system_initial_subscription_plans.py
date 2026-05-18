import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models.plan import SubscriptionPlan


DATA_FILENAME = "seed_system_initial_subscription_plans.json"


class Command(BaseCommand):
    help = f"Cria os 3 planos de assinatura base (Individual, Fidelidade, Família) a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_subscription_plans"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhum plano encontrado no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                code = entry.get("code", "").strip()
                if not code:
                    raise CommandError(f"Entrada inválida no JSON: 'code' é obrigatório. Entrada: {entry}")

                plan, created = SubscriptionPlan.objects.get_or_create(
                    code=code,
                    defaults=self._build_defaults(entry),
                )
                if not created:
                    self._apply_updates(plan, entry)
                    plan.save()

                status = "criado" if created else "atualizado"
                self.stdout.write(f"  [{status}] {plan.display_name} (code={code})")

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPlanos base: {created_count} criado(s), {updated_count} atualizado(s)."
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
            "is_family_plan": entry.get("is_family_plan", False),
            "is_loyalty_plan": entry.get("is_loyalty_plan", False),
            "description": entry.get("description", ""),
            "display_order": entry.get("display_order", 0),
            "is_active": entry.get("is_active", True),
        }

    def _apply_updates(self, plan: SubscriptionPlan, entry: dict) -> None:
        plan.display_name = entry["display_name"]
        plan.audience = entry.get("audience", "adult")
        plan.is_family_plan = entry.get("is_family_plan", False)
        plan.is_loyalty_plan = entry.get("is_loyalty_plan", False)
        plan.description = entry.get("description", "")
        plan.display_order = entry.get("display_order", 0)
        plan.is_active = entry.get("is_active", True)
