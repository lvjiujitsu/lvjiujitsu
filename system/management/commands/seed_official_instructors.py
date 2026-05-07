from django.core.management.base import BaseCommand, CommandError

from system.services.seeding import SeedDependencyError, seed_official_instructors


class Command(BaseCommand):
    help = "Cria ou atualiza apenas os professores oficiais e suas contas de portal."

    def handle(self, *args, **options):
        try:
            result = seed_official_instructors()
        except SeedDependencyError as exc:
            raise CommandError(str(exc)) from exc

        teachers = result["teachers"]
        self.stdout.write(f"Professores oficiais cadastrados: {len(teachers)}")
        for teacher in teachers.values():
            graduation = teacher.graduations.order_by("-awarded_at", "-created_at").first()
            graduation_label = (
                f"{graduation.belt_rank.display_name} grau {graduation.grade_number}"
                if graduation
                else "sem graduação"
            )
            portal_label = "portal ativo" if teacher.has_portal_access else "sem portal"
            self.stdout.write(
                f"- {teacher.cpf}: {teacher.full_name} | {portal_label} | faixa {graduation_label}"
            )
        self.stdout.write(self.style.SUCCESS("Seed de professores oficiais concluída."))
