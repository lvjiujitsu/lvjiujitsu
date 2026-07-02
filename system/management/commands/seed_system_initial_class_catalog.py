import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import ClassCategory, ClassGroup, ClassSchedule, Person
from system.utils import format_cpf_digits


DATA_FILENAME = "seed_system_initial_class_catalog.json"


class Command(BaseCommand):
    help = f"Cria turmas e horários a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_class_catalog"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhuma turma encontrada no arquivo {DATA_FILENAME}."))
            return

        groups_created = 0
        groups_updated = 0
        schedules_created = 0

        with transaction.atomic():
            for entry in data:
                category = self._get_category(entry["class_category"])
                teacher = self._get_teacher(entry["teacher"]["cpf"], entry["teacher"]["full_name"])

                group, created = ClassGroup.objects.get_or_create(
                    class_category=category,
                    main_teacher=teacher,
                    defaults={
                        "display_name": entry["display_name"],
                        "description": entry.get("description", ""),
                    },
                )
                if not created:
                    group.display_name = entry["display_name"]
                    group.description = entry.get("description", "")
                    group.save()

                status = "criado" if created else "atualizado"
                self.stdout.write(
                    f"  [{status}] {group.display_name} / {category.display_name} — prof. {teacher.full_name}"
                )
                if created:
                    groups_created += 1
                else:
                    groups_updated += 1

                sc = self._sync_schedules(group, entry.get("schedules", []))
                schedules_created += sc
                if sc:
                    self.stdout.write(f"    -> {sc} horário(s) criado(s)")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTurmas: {groups_created} criada(s), {groups_updated} atualizada(s). "
                f"Horários: {schedules_created} criado(s)."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_category(self, code: str) -> ClassCategory:
        try:
            return ClassCategory.objects.get(code=code)
        except ClassCategory.DoesNotExist:
            raise CommandError(
                f"Categoria '{code}' não encontrada. "
                "Execute 'seed_system_initial_class_categories' antes desta seed."
            )

    def _get_teacher(self, raw_cpf: str, full_name: str) -> Person:
        cpf = format_cpf_digits(raw_cpf)
        try:
            return Person.objects.get(cpf=cpf)
        except Person.DoesNotExist:
            raise CommandError(
                f"Professor '{full_name}' (CPF {cpf}) não encontrado. "
                "Execute 'seed_system_initial_teacher' antes desta seed."
            )

    def _sync_schedules(self, group: ClassGroup, schedules: list) -> int:
        created_count = 0
        for sched in schedules:
            _, created = ClassSchedule.objects.get_or_create(
                class_group=group,
                weekday=sched["weekday"],
                training_style=sched["training_style"],
                start_time=sched["start_time"],
                defaults={"display_order": sched.get("display_order", 0)},
            )
            if created:
                created_count += 1
        return created_count
