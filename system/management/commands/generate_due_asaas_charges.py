from django.core.management.base import BaseCommand

from system.services.asaas_billing_cycle import generate_due_asaas_charges


class Command(BaseCommand):
    help = (
        "Gera a cobrança Asaas do próximo ciclo para memberships PIX/cartão "
        "cujo current_period_end está vencendo, usando o valor já correto "
        "(billed_price com desconto família, quando aplicável). Idempotente — "
        "não duplica cobrança se já existir pedido pendente para o mesmo ciclo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--lead-days",
            type=int,
            default=3,
            help="Quantos dias antes do vencimento gerar a cobrança (padrão: 3).",
        )

    def handle(self, *args, **options):
        lead_days = options["lead_days"]
        result = generate_due_asaas_charges(lead_days=lead_days)
        generated = result["generated"]
        skipped = result["skipped"]

        for order in generated:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cobrança gerada: pedido #{order.pk} — {order.person.full_name} — "
                    f"R$ {order.total}"
                )
            )
        for membership in skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"Falha ao gerar cobrança para membership #{membership.pk} "
                    f"({membership.person.full_name}) — ver log."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído: {len(generated)} cobrança(s) gerada(s), "
                f"{len(skipped)} pulada(s) por falha."
            )
        )
