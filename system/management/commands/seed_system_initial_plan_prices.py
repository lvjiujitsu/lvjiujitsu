import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models.plan import BillingCycle, PlanPaymentMethod, PlanPrice, PlanTier


DATA_FILENAME = "seed_system_initial_plan_prices.json"


class Command(BaseCommand):
    help = f"Cria os preços por tier x forma de pagamento x ciclo a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_plan_prices"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhum preço encontrado no arquivo {DATA_FILENAME}."))
            return

        sync_enabled = getattr(settings, "STRIPE_PLAN_SYNC_ENABLED", False)
        if sync_enabled and not getattr(settings, "STRIPE_SECRET_KEY", ""):
            raise CommandError("STRIPE_PLAN_SYNC_ENABLED=True mas STRIPE_SECRET_KEY não configurada no .env.")

        created_count = 0
        updated_count = 0
        synced_count = 0

        with transaction.atomic():
            for entry in data:
                price, created = self._upsert_price(entry)
                status = "criado" if created else "atualizado"
                self.stdout.write(
                    f"  [{status}] {price.tier.display_name} - {price.get_payment_method_display()} "
                    f"({price.get_billing_cycle_display()}) - R$ {price.price} (gateway={price.gateway_code})"
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                if sync_enabled and price.gateway_code == "stripe_card":
                    self._sync_to_stripe(price)
                    synced_count += 1

        summary = f"\nPreços de plano: {created_count} criado(s), {updated_count} atualizado(s)"
        if sync_enabled:
            summary += f", {synced_count} sincronizado(s) com o Stripe."
        else:
            summary += ". Sincronização Stripe desabilitada (STRIPE_PLAN_SYNC_ENABLED não definida)."
        self.stdout.write(self.style.SUCCESS(summary))

    def _sync_to_stripe(self, price):
        from system.services.stripe_sync import StripeSyncError, sync_plan_to_stripe

        try:
            synced = sync_plan_to_stripe(price)
            self.stdout.write(
                f"    -> Stripe sincronizado: product={synced.stripe_product_id} price={synced.stripe_price_id}"
            )
        except StripeSyncError as exc:
            self.stdout.write(self.style.WARNING(f"    -> Falha na sincronização Stripe: {exc}"))

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _upsert_price(self, entry: dict):
        tier_code = self._required(entry, "tier_code")
        try:
            tier = PlanTier.objects.get(code=tier_code)
        except PlanTier.DoesNotExist as exc:
            raise CommandError(
                f"PlanTier '{tier_code}' não encontrado. Rode seed_system_initial_plan_tiers antes."
            ) from exc

        billing_cycle = self._required(entry, "billing_cycle")
        if billing_cycle not in BillingCycle.values:
            raise CommandError(f"Ciclo inválido: {billing_cycle}")
        payment_method = self._required(entry, "payment_method")
        if payment_method not in PlanPaymentMethod.values:
            raise CommandError(f"Forma de pagamento inválida: {payment_method}")
        gateway_code = self._required(entry, "gateway_code")

        defaults = {
            "payment_method": payment_method,
            "base_monthly_net_price": self._decimal(entry, "base_monthly_net_price"),
            "cycle_discount_percentage": self._percentage(entry, "cycle_discount_percentage"),
            "gateway_fixed_fee": self._decimal(entry, "gateway_fixed_fee"),
            "gateway_percentage_fee": self._percentage(entry, "gateway_percentage_fee"),
        }

        price, created = PlanPrice.objects.update_or_create(
            tier=tier,
            gateway_code=gateway_code,
            billing_cycle=billing_cycle,
            defaults=defaults,
        )
        return price, created

    def _required(self, entry: dict, field_name: str) -> str:
        value = entry.get(field_name, "")
        if not isinstance(value, str) or not value.strip():
            raise CommandError(f"Entrada inválida no JSON: '{field_name}' é obrigatório. Entrada: {entry}")
        return value.strip()

    def _decimal(self, entry: dict, field_name: str) -> Decimal:
        try:
            return Decimal(str(entry[field_name]).replace(",", ".")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"Entrada inválida no JSON: '{field_name}' deve ser decimal. Entrada: {entry}") from exc

    def _percentage(self, entry: dict, field_name: str) -> Decimal:
        return (self._decimal(entry, field_name) / Decimal("100")).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
        )
