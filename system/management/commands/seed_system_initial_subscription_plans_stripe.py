import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models.plan import (
    BillingCycle,
    CYCLE_MONTHS,
    PlanAudience,
    PlanPaymentMethod,
    SubscriptionPlan,
)


DATA_FILENAME = "seed_system_initial_subscription_plans_stripe.json"
SUPPORTED_GATEWAY = "stripe_card"

CATEGORY_AUDIENCE = {
    "individual": PlanAudience.ADULT,
    "loyalty": PlanAudience.ADULT,
    "family": PlanAudience.ADULT,
    "kids": PlanAudience.KIDS_JUVENILE,
}


class Command(BaseCommand):
    help = (
        f"Cria planos Stripe Subscriptions a partir de static/initial_data/{DATA_FILENAME}. "
        "Com STRIPE_PLAN_SYNC_ENABLED=True sincroniza Product/Price no Stripe."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_subscription_plans_stripe"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhum plano encontrado em {DATA_FILENAME}."))
            return

        sync_enabled = getattr(settings, "STRIPE_PLAN_SYNC_ENABLED", False)
        if sync_enabled and not getattr(settings, "STRIPE_SECRET_KEY", ""):
            raise CommandError("STRIPE_PLAN_SYNC_ENABLED=True mas STRIPE_SECRET_KEY não configurada no .env.")

        created_count = 0
        updated_count = 0
        synced_count = 0

        # Códigos válidos para este seed (somente ciclo mensal)
        valid_codes: list[str] = []
        for entry in data:
            for billing_cycle in self._get_cycles(entry):
                valid_codes.append(self._build_code(entry, billing_cycle))

        with transaction.atomic():
            # Inativar planos Stripe de ciclos não-mensais que possam existir de seeds anteriores
            stale_qs = SubscriptionPlan.objects.filter(
                gateway_code=SUPPORTED_GATEWAY,
                is_active=True,
            ).exclude(code__in=valid_codes)
            stale_count = stale_qs.count()
            if stale_count:
                stale_qs.update(is_active=False)
                self.stdout.write(
                    self.style.WARNING(
                        f"  [inativado] {stale_count} plano(s) Stripe com ciclos obsoletos "
                        f"(quarterly/semiannual/annual) removidos do catálogo ativo."
                    )
                )

            for entry in data:
                for billing_cycle, cycle_data in self._get_cycles(entry).items():
                    plan, created = self._upsert_plan(entry, billing_cycle, cycle_data)
                    status = "criado" if created else "atualizado"
                    self.stdout.write(
                        f"  [{status}] {plan.display_name} — R$ {plan.price}/mês (code={plan.code})"
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    if sync_enabled:
                        self._sync_to_stripe(plan)
                        synced_count += 1

        summary = (
            f"\nPlanos Stripe: {created_count} criado(s), {updated_count} atualizado(s)"
        )
        if sync_enabled:
            summary += f", {synced_count} sincronizado(s) com o Stripe."
        else:
            summary += ". Sincronização Stripe desabilitada (STRIPE_PLAN_SYNC_ENABLED não definida)."
        self.stdout.write(self.style.SUCCESS(summary))

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_cycles(self, entry: dict) -> dict:
        cycles = entry.get("cycles")
        if not isinstance(cycles, dict) or not cycles:
            raise CommandError(f"Entrada inválida: 'cycles' é obrigatório. Entrada: {entry}")
        invalid_cycles = set(cycles) - set(BillingCycle.values)
        if invalid_cycles:
            raise CommandError(f"Ciclo(s) inválido(s): {sorted(invalid_cycles)}")
        return cycles

    def _upsert_plan(self, entry: dict, billing_cycle: str, cycle_data: dict):
        code = self._build_code(entry, billing_cycle)
        charged_price = self._decimal(cycle_data, "charged_price")
        n_months = CYCLE_MONTHS[billing_cycle]
        monthly_reference_price = None
        if n_months > 1:
            monthly_reference_price = (charged_price / Decimal(str(n_months))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        category_code = self._required(entry, "category_code")
        audience = CATEGORY_AUDIENCE.get(category_code, PlanAudience.ADULT)

        defaults = {
            "display_name": self._build_display_name(entry, billing_cycle),
            "audience": audience,
            "weekly_frequency": self._integer(entry, "weekly_frequency"),
            "billing_cycle": billing_cycle,
            "payment_method": PlanPaymentMethod.CREDIT_CARD,
            "is_family_plan": category_code == "family",
            "is_loyalty_plan": category_code == "loyalty",
            "base_monthly_net_price": self._decimal(entry, "base_monthly_net_price"),
            "gateway_code": SUPPORTED_GATEWAY,
            "gateway_fixed_fee": self._decimal(entry, "gateway_fixed_fee"),
            "gateway_percentage_fee": self._percentage(entry, "gateway_percentage_fee"),
            "cycle_discount_percentage": self._percentage(cycle_data, "discount_percentage"),
            "description": self._build_description(entry, cycle_data),
            "display_order": self._build_display_order(entry, billing_cycle),
            "is_active": True,
        }

        plan, created = SubscriptionPlan.objects.update_or_create(code=code, defaults=defaults)
        SubscriptionPlan.objects.filter(pk=plan.pk).update(
            price=charged_price,
            monthly_reference_price=monthly_reference_price,
        )
        plan.refresh_from_db()
        return plan, created

    def _sync_to_stripe(self, plan):
        from system.services.stripe_sync import StripeSyncError, sync_plan_to_stripe

        try:
            synced = sync_plan_to_stripe(plan)
            self.stdout.write(
                f"    -> Stripe sincronizado: product={synced.stripe_product_id} price={synced.stripe_price_id}"
            )
        except StripeSyncError as exc:
            self.stdout.write(self.style.WARNING(f"    -> Falha na sincronização Stripe: {exc}"))

    def _build_code(self, entry: dict, billing_cycle: str) -> str:
        category_code = self._required(entry, "category_code")
        weekly_frequency = self._integer(entry, "weekly_frequency")
        return f"{category_code}-{weekly_frequency}x-stripe-card-{billing_cycle}"

    def _build_display_name(self, entry: dict, billing_cycle: str) -> str:
        return (
            f"{self._required(entry, 'category_name')} "
            f"{self._integer(entry, 'weekly_frequency')}x por semana - "
            f"Stripe Cartão - Assinatura Recorrente Mensal"
        )

    def _build_description(self, entry: dict, cycle_data: dict) -> str:
        return (
            f"Assinatura recorrente mensal via Stripe. "
            f"Cobrança automática de R$ {self._decimal(cycle_data, 'charged_price')} todo mês. "
            f"Líquido mensal: R$ {self._decimal(cycle_data, 'monthly_net_price')}. "
            f"Permanência mínima de 12 meses — sem cancelamento ou trancamento durante o período."
        )

    def _build_display_order(self, entry: dict, billing_cycle: str) -> int:
        category_order = {
            "individual": 100,
            "loyalty": 200,
            "family": 300,
            "kids": 400,
        }.get(self._required(entry, "category_code"), 900)
        cycle_order = {
            BillingCycle.MONTHLY: 1,
            BillingCycle.QUARTERLY: 2,
            BillingCycle.SEMIANNUAL: 3,
            BillingCycle.ANNUAL: 4,
        }[billing_cycle]
        return category_order + (self._integer(entry, "weekly_frequency") * 10) + 3 + cycle_order

    def _required(self, entry: dict, field_name: str) -> str:
        value = entry.get(field_name, "")
        if not isinstance(value, str) or not value.strip():
            raise CommandError(f"'{field_name}' é obrigatório. Entrada: {entry}")
        return value.strip()

    def _integer(self, entry: dict, field_name: str) -> int:
        try:
            return int(entry[field_name])
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"'{field_name}' deve ser inteiro. Entrada: {entry}") from exc

    def _decimal(self, entry: dict, field_name: str) -> Decimal:
        try:
            return Decimal(str(entry[field_name]).replace(",", ".")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"'{field_name}' deve ser decimal. Entrada: {entry}") from exc

    def _percentage(self, entry: dict, field_name: str) -> Decimal:
        return (self._decimal(entry, field_name) / Decimal("100")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
