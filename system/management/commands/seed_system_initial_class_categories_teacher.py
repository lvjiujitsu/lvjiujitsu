import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import ClassCategory, Person


class Command(BaseCommand):
    help = "Vincula professores à sua categoria de turma principal (Person.class_category)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_class_categories_teacher"))
        data = self._load_json()

        entries_with_category = [e for e in data if e.get("class_category")]
        if not entries_with_category:
            self.stdout.write(self.style.WARNING(
                "Nenhum professor com 'class_category' definido em initial_teachers.json."
            ))
            return

        linked_count = 0
        skipped_count = 0

        with transaction.atomic():
            for entry in entries_with_category:
                cpf = entry.get("cpf", "").strip()
                category_code = entry["class_category"].strip()

                person = self._get_person(cpf)
                category = self._get_category(category_code)

                if person.class_category_id == category.pk:
                    self.stdout.write(f"  [sem alteração] {person.full_name} -> {category.display_name}")
                    skipped_count += 1
                    continue

                person.class_category = category
                person.save(update_fields=["class_category", "updated_at"])
                self.stdout.write(f"  [vinculado] {person.full_name} -> {category.display_name}")
                linked_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nProfessores: {linked_count} vinculado(s), {skipped_count} sem alteração."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / "initial_teachers.json"
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_person(self, cpf: str) -> Person:
        try:
            return Person.objects.get(cpf=cpf)
        except Person.DoesNotExist:
            raise CommandError(
                f"Professor com CPF '{cpf}' não encontrado. "
                "Execute 'seed_system_initial_teacher' antes desta seed."
            )

    def _get_category(self, code: str) -> ClassCategory:
        try:
            return ClassCategory.objects.get(code=code)
        except ClassCategory.DoesNotExist:
            raise CommandError(
                f"Categoria '{code}' não encontrada. "
                "Execute 'seed_system_initial_class_categories' antes desta seed."
            )
