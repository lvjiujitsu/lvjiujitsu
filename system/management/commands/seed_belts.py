from django.core.management.base import BaseCommand

from system.services.seeding import seed_belts


class Command(BaseCommand):
    help = "Cria ou atualiza apenas as faixas de graduação padrão."

    def handle(self, *args, **options):
        result = seed_belts()
        belts = result["belts"]
        self.stdout.write(f"Faixas cadastradas: {len(belts)}")
        for belt in belts.values():
            next_code = belt.next_rank.code if belt.next_rank else "-"
            self.stdout.write(
                f"- {belt.code}: {belt.display_name} | público {belt.get_audience_display()} | "
                f"graus {belt.max_grades} | próxima {next_code}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de faixas concluída."))
