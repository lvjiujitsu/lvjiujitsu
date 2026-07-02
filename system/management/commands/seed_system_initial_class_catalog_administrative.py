import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import Person
from system.services.administrative_training import (
    enrollment_specs,
    instructor_assignment_specs,
    sync_administrative_training_links,
)
from system.utils import format_cpf_digits


class Command(BaseCommand):
    help = (
        "Reaplica vínculos de treino dos administrativos a partir de "
        "static/initial_data/initial_administrative.json. "
        "Preferencialmente já executado por seed_system_initial_administrative."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_class_catalog_administrative"))
        data = self._load_json()

        entries = [
            entry for entry in data
            if enrollment_specs(entry) or instructor_assignment_specs(entry) or entry.get("class_category")
        ]
        if not entries:
            self.stdout.write(self.style.WARNING(
                "Nenhum administrativo com turmas definidas em initial_administrative.json."
            ))
            return

        linked_count = 0

        with transaction.atomic():
            for entry in entries:
                cpf = format_cpf_digits(entry.get("cpf", "").strip())
                person = self._get_person(cpf)
                try:
                    summary = sync_administrative_training_links(person, entry)
                except ObjectDoesNotExist as exc:
                    raise CommandError(str(exc)) from exc

                labels = []
                if summary.get("enrollment_groups"):
                    labels.extend(
                        f"matrícula {group.display_name}/{group.class_category.display_name}"
                        for group in summary["enrollment_groups"]
                    )
                if summary.get("assignment_groups"):
                    labels.extend(
                        f"apoio {group.display_name}/{group.class_category.display_name}"
                        for group in summary["assignment_groups"]
                    )
                if summary.get("category"):
                    labels.append(f"categoria {summary['category']}")
                self.stdout.write(f"  [vinculado] {person.full_name} -> {', '.join(labels)}")
                linked_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nAdministrativos: {linked_count} vínculo(s) reaplicado(s).")
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
