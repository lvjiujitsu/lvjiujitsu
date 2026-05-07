from django.core.management.base import BaseCommand, CommandError

from system.services.seeding import SeedDependencyError, seed_teacher_payroll_configs


class Command(BaseCommand):
    help = "Cria ou atualiza apenas as configurações de repasse dos professores."

    def handle(self, *args, **options):
        try:
            result = seed_teacher_payroll_configs()
        except SeedDependencyError as exc:
            raise CommandError(str(exc)) from exc

        entries = result["entries"]
        self.stdout.write(f"Configurações de repasse cadastradas: {len(entries)}")
        for entry in entries:
            person = entry["person"]
            config = entry["config"]
            self.stdout.write(
                f"- {person.full_name}: salário R$ {config.monthly_salary:.2f} | "
                f"dia {config.payment_day} | regras {entry['rules_count']}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de repasses de professores concluída."))
