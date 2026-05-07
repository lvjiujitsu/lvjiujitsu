from django.core.management.base import BaseCommand, CommandError

from system.services.seeding import SeedDependencyError, seed_graduation_rules


class Command(BaseCommand):
    help = "Cria ou atualiza apenas as regras de graduação padrão."

    def handle(self, *args, **options):
        try:
            result = seed_graduation_rules()
        except SeedDependencyError as exc:
            raise CommandError(str(exc)) from exc

        rules = result["rules"]
        self.stdout.write(f"Regras de graduação cadastradas: {len(rules)}")
        for rule in rules.values():
            target = f"grau {rule.to_grade}" if rule.to_grade is not None else "próxima faixa"
            self.stdout.write(
                f"- {rule.belt_rank.code} grau {rule.from_grade} -> {target} | "
                f"meses {rule.min_months_in_current_grade} | "
                f"aulas {rule.min_classes_required}/{rule.min_classes_window_months}m"
            )
        self.stdout.write(self.style.SUCCESS("Seed de regras de graduação concluída."))
