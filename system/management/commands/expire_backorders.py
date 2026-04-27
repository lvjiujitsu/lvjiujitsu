from django.core.management.base import BaseCommand

from system.services.product_backorders import expire_pending_reservations


class Command(BaseCommand):
    help = "Marca pré-pedidos READY com prazo vencido como EXPIRED e promove a fila."

    def handle(self, *args, **options):
        result = expire_pending_reservations()
        if not result:
            self.stdout.write(self.style.WARNING("Nenhuma reserva expirada encontrada."))
            return
        expired_count = len(result.get("expired", []))
        promoted_count = len(result.get("promoted", []))
        self.stdout.write(
            self.style.SUCCESS(
                f"{expired_count} reserva(s) expirada(s); {promoted_count} promovida(s) da fila."
            )
        )
