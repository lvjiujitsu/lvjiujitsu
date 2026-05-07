from django.core.management.base import BaseCommand

from system.services.seeding import seed_plans


class Command(BaseCommand):
    help = "Cria ou atualiza os planos de assinatura."

    def handle(self, *args, **options):
        result = seed_plans()
        self.stdout.write(f"Planos cadastrados: {len(result)}")
        for plan in result.values():
            self.stdout.write(f"- {plan.code}: {plan.display_name} | R$ {plan.price:.2f}")
        self.stdout.write(self.style.SUCCESS("Seed de planos concluída."))
