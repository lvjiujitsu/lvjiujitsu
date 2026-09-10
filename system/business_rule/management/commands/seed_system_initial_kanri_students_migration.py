from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from system.business_rule.services.kanri_migration.graduations import KanriGraduationMixin
from system.business_rule.services.kanri_migration.identity import KanriIdentityMixin
from system.business_rule.services.kanri_migration.people import KanriPeopleMixin
from system.business_rule.services.kanri_migration.relationships import KanriRelationshipMixin
from system.business_rule.services.kanri_migration.source import KanriSourceMixin
from system.business_rule.services.kanri_migration.stats import KanriStatsMixin
from system.business_rule.services.kanri_migration.values import KanriValueMixin
from system.business_rule.services.kanri_migration.constants import DATA_DIRNAME


class Command(
    KanriGraduationMixin,
    KanriIdentityMixin,
    KanriPeopleMixin,
    KanriRelationshipMixin,
    KanriSourceMixin,
    KanriStatsMixin,
    KanriValueMixin,
    BaseCommand,
):
    help = (
        "Importa alunos, responsáveis, dependentes e graduações a partir dos JSONs "
        f"em static/business_rule/initial_data/{DATA_DIRNAME}/."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_kanri_students_migration"))

        records = self._load_records()
        if not records:
            self.stdout.write(
                self.style.WARNING(f"Nenhum arquivo JSON encontrado em {DATA_DIRNAME}.")
            )
            return

        person_types = self._get_person_types()
        student_document_counts = Counter(
            record["student_document"]
            for record in records
            if record["student_document"]
        )
        belt_ranks = self._get_belt_ranks(records)
        stats = self._empty_stats()

        with transaction.atomic():
            for record in records:
                self._sync_record(
                    record=record,
                    person_types=person_types,
                    student_document_counts=student_document_counts,
                    belt_ranks=belt_ranks,
                    stats=stats,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "\nKanri: "
                f"{stats['persons_created']} pessoa(s) criada(s), "
                f"{stats['persons_updated']} pessoa(s) atualizada(s), "
                f"{stats['relationships_created']} vínculo(s) criado(s), "
                f"{stats['relationships_updated']} vínculo(s) atualizado(s), "
                f"{stats['graduations_created']} graduação(ões) criada(s), "
                f"{stats['migration_cpfs']} CPF substituto(s), "
                f"{stats['financial_skipped']} financeiro não importado(s), "
                f"{stats['attendance_skipped']} histórico de aulas não importado(s)."
            )
        )

