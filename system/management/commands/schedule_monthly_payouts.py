from datetime import date

from django.core.management.base import BaseCommand

from system.services.asaas_payroll import schedule_monthly_payouts


class Command(BaseCommand):
    help = "Cria TeacherPayouts pendentes para configs ativas cujo payment_day é hoje."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="target_date",
            default=None,
            help="Data de referência no formato AAAA-MM-DD (default: hoje)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Simula sem criar pagamentos.",
        )

    def handle(self, *args, **options):
        target = None
        if options.get("target_date"):
            target = date.fromisoformat(options["target_date"])
        result = schedule_monthly_payouts(today=target, dry_run=options["dry_run"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Folha processada: {len(result)} pagamento(s) {'simulado(s)' if options['dry_run'] else 'criado(s)'}."
            )
        )
        for item in result:
            self.stdout.write(f"  - {item}")
