import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.business_rule.models.plan import (
    BillingCycle,
    CYCLE_MONTHS,
    PlanAudience,
    PlanPaymentMethod,
    SubscriptionPlan,
)


DATA_FILENAME = "seed_system_initial_subscription_plans_values.json"
BASE_PLACEHOLDER_CODES = ("individual", "loyalty", "family")
SUPPORTED_GATEWAYS = ("asaas_pix", "asaas_card")


class Command(BaseCommand):
    help = f"Cria os valores cobrados dos planos a partir de static/business_rule/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_subscription_plans_values"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhum valor de plano encontrado no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0
        valid_codes: list[str] = []

        with transaction.atomic():
            for entry in data:
                for billing_cycle, cycle_data in self._get_cycles(entry).items():
                    plan, created = self._upsert_plan(entry, billing_cycle, cycle_data)
                    valid_codes.append(plan.code)
                    status = "criado" if created else "atualizado"
                    self.stdout.write(
                        f"  [{status}] {plan.display_name} - R$ {plan.price} (code={plan.code})"
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            deactivated_count = SubscriptionPlan.objects.filter(
                code__in=BASE_PLACEHOLDER_CODES,
                is_active=True,
            ).update(is_active=False)

            stale_qs = SubscriptionPlan.objects.filter(
                gateway_code__in=SUPPORTED_GATEWAYS,
                is_active=True,
            ).exclude(code__in=valid_codes)
            stale_count = stale_qs.count()
            if stale_count:
                stale_qs.update(is_active=False)
                self.stdout.write(
                    self.style.WARNING(
                        f"  [inativado] {stale_count} plano(s) Asaas obsoleto(s) "
                        "(fora do JSON atual, ex: Veterano 2x)."
                    )
                )
                deactivated_count += stale_count

        self.stdout.write(
            self.style.SUCCESS(
                "\nValores de planos: "
                f"{created_count} criado(s), {updated_count} atualizado(s), "
                f"{deactivated_count} plano(s) inativado(s)."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "business_rule" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_cycles(self, entry: dict) -> dict:
        cycles = entry.get("cycles")
        if not isinstance(cycles, dict) or not cycles:
            raise CommandError(f"Entrada inválida no JSON: 'cycles' é obrigatório. Entrada: {entry}")
        invalid_cycles = set(cycles) - set(BillingCycle.values)
        if invalid_cycles:
            raise CommandError(f"Ciclo(s) inválido(s) no JSON: {sorted(invalid_cycles)}")
        return cycles

    def _upsert_plan(self, entry: dict, billing_cycle: str, cycle_data: dict):
        code = self._build_code(entry, billing_cycle)
        charged_price = self._decimal(cycle_data, "charged_price")
        n_months = CYCLE_MONTHS[billing_cycle]
        monthly_reference_price = None
        if n_months > 1:
            monthly_reference_price = (charged_price / Decimal(str(n_months))).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        base_monthly_net_price = self._decimal(
            cycle_data if "base_monthly_net_price" in cycle_data else entry,
            "base_monthly_net_price",
        )

        defaults = {
            "display_name": self._build_display_name(entry, billing_cycle),
            "audience": PlanAudience.ADULT,
            "weekly_frequency": self._integer(entry, "weekly_frequency"),
            "billing_cycle": billing_cycle,
            "payment_method": self._payment_method(entry),
            "is_family_plan": entry["category_code"] == "family",
            "is_loyalty_plan": entry["category_code"] == "loyalty",
            "base_monthly_net_price": base_monthly_net_price,
            "gateway_code": self._required(entry, "gateway_code"),
            "gateway_fixed_fee": self._decimal(entry, "gateway_fixed_fee"),
            "gateway_percentage_fee": self._percentage(entry, "gateway_percentage_fee"),
            "cycle_discount_percentage": self._percentage(cycle_data, "discount_percentage"),
            "description": self._build_description(entry, cycle_data),
            "display_order": self._build_display_order(entry, billing_cycle),
            "is_active": True,
        }

        plan, created = SubscriptionPlan.objects.update_or_create(
            code=code,
            defaults=defaults,
        )
        SubscriptionPlan.objects.filter(pk=plan.pk).update(
            price=charged_price,
            monthly_reference_price=monthly_reference_price,
        )
        plan.refresh_from_db()
        return plan, created

    def _build_code(self, entry: dict, billing_cycle: str) -> str:
        category_code = self._required(entry, "category_code")
        weekly_frequency = self._integer(entry, "weekly_frequency")
        gateway_slug = self._gateway_code(entry).replace("_", "-")
        return f"{category_code}-{weekly_frequency}x-{gateway_slug}-{billing_cycle}"

    def _build_display_name(self, entry: dict, billing_cycle: str) -> str:
        return (
            f"{self._required(entry, 'category_name')} "
            f"{self._integer(entry, 'weekly_frequency')}x por semana - "
            f"{self._required(entry, 'gateway_name')} "
            f"{self._required(entry, 'payment_label')} - "
            f"{BillingCycle(billing_cycle).label}"
        )

    def _build_description(self, entry: dict, cycle_data: dict) -> str:
        base_source = cycle_data if "base_monthly_net_price" in cycle_data else entry
        return (
            f"Valor líquido mensal desejado: R$ {self._decimal(base_source, 'base_monthly_net_price')}. "
            f"Líquido mensal estimado no ciclo: R$ {self._decimal(cycle_data, 'monthly_net_price')}."
        )

    def _build_display_order(self, entry: dict, billing_cycle: str) -> int:
        category_order = {
            "individual": 100,
            "loyalty": 200,
            "family": 300,
        }.get(self._required(entry, "category_code"), 900)
        gateway_order = {
            "asaas_pix": 1,
            "asaas_card": 2,
        }.get(self._gateway_code(entry), 9)
        cycle_order = {
            BillingCycle.MONTHLY: 1,
            BillingCycle.QUARTERLY: 2,
            BillingCycle.SEMIANNUAL: 3,
            BillingCycle.ANNUAL: 4,
        }[billing_cycle]
        return category_order + (self._integer(entry, "weekly_frequency") * 10) + gateway_order + cycle_order

    def _payment_method(self, entry: dict) -> str:
        payment_method = self._required(entry, "payment_method")
        if payment_method not in PlanPaymentMethod.values:
            raise CommandError(f"Forma de pagamento inválida: {payment_method}")
        return payment_method

    def _gateway_code(self, entry: dict) -> str:
        gateway_code = self._required(entry, "gateway_code")
        if gateway_code not in SUPPORTED_GATEWAYS:
            raise CommandError(
                f"Gateway inválido: {gateway_code}. Gateways suportados: {', '.join(SUPPORTED_GATEWAYS)}"
            )
        return gateway_code

    def _required(self, entry: dict, field_name: str) -> str:
        value = entry.get(field_name, "")
        if not isinstance(value, str) or not value.strip():
            raise CommandError(f"Entrada inválida no JSON: '{field_name}' é obrigatório. Entrada: {entry}")
        return value.strip()

    def _integer(self, entry: dict, field_name: str) -> int:
        try:
            return int(entry[field_name])
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"Entrada inválida no JSON: '{field_name}' deve ser inteiro. Entrada: {entry}") from exc

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
