from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Executa EXPLAIN local das queries representativas dos índices P2 (PRD-142 §6)."

    def handle(self, *args, **options):
        vendor = connection.vendor
        queries = [
            (
                "registration_order_person_payment",
                """
                EXPLAIN QUERY PLAN
                SELECT id FROM business_rule_registrationorder
                WHERE person_id = 1 AND payment_status = 'paid'
                """,
            ),
            (
                "class_session_date",
                """
                EXPLAIN QUERY PLAN
                SELECT id FROM business_rule_classsession
                WHERE date = '2026-04-01'
                """,
            ),
            (
                "graduation_person_awarded",
                """
                EXPLAIN QUERY PLAN
                SELECT id FROM business_rule_graduation
                WHERE person_id = 1
                ORDER BY awarded_at DESC
                LIMIT 1
                """,
            ),
        ]

        self.stdout.write(f"Database vendor: {vendor}")
        if vendor != "sqlite":
            self.stdout.write(
                self.style.WARNING(
                    "Ambiente não SQLite: substitua por EXPLAIN (ANALYZE, BUFFERS) em HG/produção."
                )
            )

        with connection.cursor() as cursor:
            for label, sql in queries:
                self.stdout.write("")
                self.stdout.write(self.style.MIGRATE_HEADING(label))
                cursor.execute(sql)
                for row in cursor.fetchall():
                    self.stdout.write("  " + " | ".join(str(part) for part in row))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("explain_perf_indexes concluído (local)."))
