from django.core.management.base import BaseCommand

from system.business_rule.services.membership_timeline_backfill import backfill_membership_timeline


class Command(BaseCommand):
    help = (
        "Popula retroativamente MembershipTimelineEvent a partir de campos de data "
        "já existentes (Membership.canceled_at, RegistrationOrder.paid_at/refunded_at, "
        "MembershipPauseRequest.created_at/decided_at). Idempotente — não duplica em "
        "execuções repetidas. Eventos sem rastro histórico confiável (dependente "
        "adicionado/removido, trocas antigas) não são reconstruídos."
    )

    def handle(self, *args, **options):
        result = backfill_membership_timeline()
        for label, count in result.items():
            self.stdout.write(self.style.SUCCESS(f"{label}: {count} evento(s) criado(s)."))
        total = sum(result.values())
        self.stdout.write(self.style.SUCCESS(f"Concluído: {total} evento(s) no total."))
