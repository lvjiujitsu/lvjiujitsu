
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.models import (
    ClassInstructorAssignment,
    Person,
    PersonOperationalRole,
    PersonRelationship,
)
from system.services.test_seed_fixtures import TEST_SEED_NOTE

CONFIRMATION = "CLEAR_TEST_DATA"
FIXTURE_FILENAMES = (
    "seed_system_initial_test_students.json",
    "seed_system_initial_test_guardians.json",
    "seed_system_initial_test_administrative.json",
    "seed_system_initial_test_teachers.json",
)


class Command(BaseCommand):
    help = (
        "Remove somente as pessoas ficticias das seeds de homologacao. "
        "Preserva as seeds iniciais de referencia."
    )

    def add_arguments(self, parser):
        parser.add_argument("--confirm", required=True)
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Confirma a remocao dos dados ficticios em producao.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["confirm"] != CONFIRMATION:
            raise CommandError(f"Confirmacao invalida. Use --confirm {CONFIRMATION}.")
        if (
            getattr(settings, "DJANGO_ENVIRONMENT", "") == "prod"
            and not options["allow_production"]
        ):
            raise CommandError(
                "Producao recusada. Repita com --allow-production para confirmar."
            )

        fixture_cpfs = self._fixture_cpfs()
        if not fixture_cpfs:
            raise CommandError("Nenhum CPF ficticio encontrado nos JSON de fixture.")

        relationships_deleted = self._delete(
            PersonRelationship.objects.filter(notes=TEST_SEED_NOTE)
        )
        roles_deleted = self._delete(
            PersonOperationalRole.objects.filter(notes=TEST_SEED_NOTE)
        )
        assignments_deleted = self._delete(
            ClassInstructorAssignment.objects.filter(notes=TEST_SEED_NOTE)
        )
        people_deleted = self._delete(Person.objects.filter(cpf__in=fixture_cpfs))

        self.stdout.write(
            self.style.SUCCESS(
                "Dados ficticios removidos: "
                f"pessoas={people_deleted}; relacionamentos={relationships_deleted}; "
                f"papeis={roles_deleted}; atribuicoes={assignments_deleted}."
            )
        )

    @staticmethod
    def _delete(queryset):
        deleted, _ = queryset.delete()
        return deleted

    @staticmethod
    def _fixture_cpfs():
        base = Path(settings.BASE_DIR) / "static" / "initial_data"
        cpfs = set()
        for filename in FIXTURE_FILENAMES:
            path = base / filename
            if not path.is_file():
                raise CommandError(f"Fixture ausente: {path}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            entries = payload if isinstance(payload, list) else payload.get("entries", [])
            cpfs.update(entry["cpf"] for entry in entries if entry.get("cpf"))
        return cpfs
