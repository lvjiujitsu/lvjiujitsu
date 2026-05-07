from django.core.management.base import BaseCommand, CommandError

from system.services.seeding import SeedDependencyError, seed_class_catalog


class Command(BaseCommand):
    help = "Cria ou atualiza apenas o catálogo base de turmas e horários."

    def handle(self, *args, **options):
        try:
            result = seed_class_catalog()
        except SeedDependencyError as exc:
            raise CommandError(str(exc)) from exc

        class_groups = result["class_groups"]
        self.stdout.write(f"Turmas cadastradas: {len(class_groups)}")
        for class_group in class_groups.values():
            schedules = list(class_group.schedules.order_by("display_order", "start_time"))
            self.stdout.write(
                f"- {class_group.code}: {class_group.display_name} | "
                f"categoria {class_group.class_category.display_name} | "
                f"professor {class_group.main_teacher.full_name} | horários {len(schedules)}"
            )
            for schedule in schedules:
                self.stdout.write(
                    f"  - {schedule.weekday} {schedule.training_style} {schedule.start_time.strftime('%H:%M')}"
                )
        self.stdout.write(self.style.SUCCESS("Seed de catálogo de turmas concluída."))
