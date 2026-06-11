import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import ClassGroup, Person
from system.utils import format_cpf_digits


class Command(BaseCommand):
    help = "Vincula administrativos à sua turma principal (Person.class_group)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_class_catalog_administrative"))
        data = self._load_json()

        entries_with_group = [e for e in data if e.get("class_group_category") and e.get("class_group_teacher_cpf")]
        if not entries_with_group:
            self.stdout.write(self.style.WARNING(
                "Nenhum administrativo com 'class_group_category' + 'class_group_teacher_cpf' "
                "definidos em initial_administrative.json."
            ))
            return

        linked_count = 0
        skipped_count = 0

        with transaction.atomic():
            for entry in entries_with_group:
                cpf = format_cpf_digits(entry.get("cpf", "").strip())
                category_code = entry["class_group_category"].strip()
                teacher_cpf = format_cpf_digits(entry["class_group_teacher_cpf"].strip())

                person = self._get_person(cpf)
                group = self._get_group(category_code, teacher_cpf)

                if person.class_group_id == group.pk:
                    self.stdout.write(
                        f"  [sem alteração] {person.full_name} → {group.display_name} "
                        f"/ {group.class_category.display_name}"
                    )
                    skipped_count += 1
                    continue

                person.class_group = group
                person.save(update_fields=["class_group", "updated_at"])
                self.stdout.write(
                    f"  [vinculado] {person.full_name} → {group.display_name} "
                    f"/ {group.class_category.display_name}"
                )
                linked_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nAdministrativos: {linked_count} vinculado(s), {skipped_count} sem alteração."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / "initial_administrative.json"
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_person(self, cpf: str) -> Person:
        try:
            return Person.objects.get(cpf=cpf)
        except Person.DoesNotExist:
            raise CommandError(
                f"Administrativo com CPF '{cpf}' não encontrado. "
                "Execute 'seed_system_initial_administrative' antes desta seed."
            )

    def _get_group(self, category_code: str, teacher_cpf: str) -> ClassGroup:
        try:
            return ClassGroup.objects.get(
                class_category__code=category_code,
                main_teacher__cpf=teacher_cpf,
            )
        except ClassGroup.DoesNotExist:
            raise CommandError(
                f"Turma não encontrada para categoria '{category_code}' e professor CPF '{teacher_cpf}'. "
                "Execute 'seed_system_initial_class_catalog' antes desta seed."
            )
        except ClassGroup.MultipleObjectsReturned:
            raise CommandError(
                f"Múltiplas turmas encontradas para categoria '{category_code}' e professor CPF '{teacher_cpf}'. "
                "Revise os dados de initial_administrative.json."
            )
