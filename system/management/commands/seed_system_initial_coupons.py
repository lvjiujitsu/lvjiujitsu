import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from system.models.coupon import Coupon


DATA_FILE = Path(settings.BASE_DIR) / "static" / "initial_data" / "seed_system_initial_coupons.json"


class Command(BaseCommand):
    help = "Cria cupons de desconto iniciais (idempotente)"

    def handle(self, *args, **options):
        if not DATA_FILE.exists():
            raise CommandError(f"Arquivo de dados não encontrado: {DATA_FILE}")

        raw = DATA_FILE.read_text(encoding="utf-8")
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommandError(f"JSON inválido em {DATA_FILE}: {exc}")

        created = 0
        updated = 0
        for entry in entries:
            code = entry.get("code", "").upper().strip()
            if not code:
                self.stdout.write(self.style.WARNING("  entrada sem code — ignorada"))
                continue

            defaults = {
                "description": entry.get("description", ""),
                "discount_type": entry.get("discount_type", "percent"),
                "discount_value": entry.get("discount_value", "0.00"),
                "max_uses": entry.get("max_uses"),
                "valid_from": entry.get("valid_from"),
                "valid_until": entry.get("valid_until"),
                "is_active": entry.get("is_active", True),
            }
            coupon, was_created = Coupon.objects.update_or_create(code=code, defaults=defaults)
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  [criado]     {coupon.code} — {coupon.description}"))
            else:
                updated += 1
                self.stdout.write(f"  [já existe]  {coupon.code} — {coupon.description}")

        self.stdout.write(self.style.SUCCESS(f"Concluído: {created} criado(s), {updated} atualizado(s)."))
