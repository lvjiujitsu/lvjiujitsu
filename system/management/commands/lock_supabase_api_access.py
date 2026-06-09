from django.core.management.base import BaseCommand
from django.db import connection

_CHECK_ROLES_SQL = """
SELECT COUNT(*) FROM pg_roles WHERE rolname IN ('anon', 'authenticated')
"""

_STATEMENTS = [
    "REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated",
    "REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated",
    "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated",
    "REVOKE ALL ON SCHEMA public FROM anon, authenticated",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES    FROM anon, authenticated",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM anon, authenticated",
]


class Command(BaseCommand):
    help = (
        "Revoga acesso das roles anon e authenticated ao schema public. "
        "Idempotente — seguro a cada deploy. "
        "Ignorado silenciosamente em SQLite ou quando as roles não existem."
    )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write("SQLite detectado — comando ignorado.")
            return

        with connection.cursor() as cursor:
            cursor.execute(_CHECK_ROLES_SQL)
            roles_found = cursor.fetchone()[0]

        if roles_found == 0:
            self.stdout.write("Roles anon/authenticated ausentes — banco não é Supabase. Comando ignorado.")
            return

        with connection.cursor() as cursor:
            for stmt in _STATEMENTS:
                cursor.execute(stmt)

        self.stdout.write(self.style.SUCCESS(
            "Acesso das roles anon/authenticated ao schema public revogado. "
            "ALTER DEFAULT PRIVILEGES aplicado — persiste no próximo ciclo destrutivo."
        ))
