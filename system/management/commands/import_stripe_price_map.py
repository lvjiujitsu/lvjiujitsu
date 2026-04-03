from django.core.management.base import BaseCommand, CommandError

from system.models import FinancialPlan
from system.services.payments.catalog import upsert_price_map_from_stripe_data
from system.services.payments.gateway import get_stripe_sdk, normalize_stripe_payload
from system.services.payments.mirror import sync_price_payload


class Command(BaseCommand):
    help = "Importa um Price real da Stripe e o vincula a um FinancialPlan local."

    def add_arguments(self, parser):
        parser.add_argument("--plan-slug", required=True, dest="plan_slug")
        parser.add_argument("--price-id", required=True, dest="price_id")
        parser.add_argument("--current", action="store_true", dest="is_current")
        parser.add_argument("--legacy", action="store_true", dest="is_legacy")
        parser.add_argument("--notes", default="", dest="notes")
        parser.add_argument(
            "--supports-pause-collection",
            action="store_true",
            dest="supports_pause_collection",
        )
        parser.add_argument(
            "--no-supports-pause-collection",
            action="store_false",
            dest="supports_pause_collection",
        )
        parser.set_defaults(supports_pause_collection=True)

    def handle(self, *args, **options):
        if options["is_current"] and options["is_legacy"]:
            raise CommandError("Um mesmo Price nao pode ser importado como vigente e legado ao mesmo tempo.")

        plan = FinancialPlan.objects.filter(slug=options["plan_slug"]).first()
        if plan is None:
            raise CommandError("Plano local nao encontrado para o slug informado.")

        sdk = get_stripe_sdk()
        try:
            price_payload = normalize_stripe_payload(
                sdk.Price.retrieve(options["price_id"], expand=["product"])
            )
        except Exception as exc:
            raise CommandError(f"Nao foi possivel consultar o Price Stripe informado: {exc}") from exc

        sync_price_payload(price_payload)
        price_map, created = upsert_price_map_from_stripe_data(
            plan=plan,
            price_payload=price_payload,
            is_current=options["is_current"],
            is_legacy=options["is_legacy"],
            supports_pause_collection=options["supports_pause_collection"],
            notes=options["notes"],
        )
        action = "criado" if created else "atualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Mapeamento {action}: plano={plan.slug} price={price_map.stripe_price_id} "
                f"current={price_map.is_current} legacy={price_map.is_legacy}"
            )
        )
