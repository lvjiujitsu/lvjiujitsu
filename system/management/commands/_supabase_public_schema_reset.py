import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


PUBLIC_RELATION_COUNT_SQL = """
SELECT COUNT(*)
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
"""

PUBLIC_RELATION_LIST_SQL = """
SELECT c.relkind, c.relname
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
ORDER BY c.relname
"""

RELKIND_LABELS = {
    "r": "tabela",
    "p": "tabela particionada",
    "v": "view",
    "m": "view materializada",
    "S": "sequence",
    "f": "foreign table",
}

PUBLIC_RELATION_RESET_SQL = """
DO $$
DECLARE
    item record;
BEGIN
    FOR item IN
        SELECT c.relkind, c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
        ORDER BY
          CASE c.relkind
            WHEN 'v' THEN 1
            WHEN 'm' THEN 2
            WHEN 'f' THEN 3
            WHEN 'r' THEN 4
            WHEN 'p' THEN 5
            WHEN 'S' THEN 6
            ELSE 7
          END
    LOOP
        IF item.relkind = 'v' THEN
            EXECUTE format('DROP VIEW IF EXISTS public.%I CASCADE', item.relname);
        ELSIF item.relkind = 'm' THEN
            EXECUTE format('DROP MATERIALIZED VIEW IF EXISTS public.%I CASCADE', item.relname);
        ELSIF item.relkind = 'f' THEN
            EXECUTE format('DROP FOREIGN TABLE IF EXISTS public.%I CASCADE', item.relname);
        ELSIF item.relkind IN ('r', 'p') THEN
            EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', item.relname);
        ELSIF item.relkind = 'S' THEN
            EXECUTE format('DROP SEQUENCE IF EXISTS public.%I CASCADE', item.relname);
        END IF;
    END LOOP;
END $$;
"""


class SupabasePublicSchemaResetCommand(BaseCommand):
    target_environment = ""
    confirmation_value = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Executa a remocao. Sem esta flag, apenas lista o alvo.",
        )

    def handle(self, *args, **options):
        project_ref = self.validate_safety_guards()
        relations = self.list_public_relations()

        self.stdout.write(f"Projeto Supabase confirmado: {project_ref}")
        self.stdout.write(
            f"Objetos encontrados no schema public: {len(relations)}"
        )
        for relkind, relname in relations:
            self.stdout.write(f"  - {RELKIND_LABELS.get(relkind, relkind)} public.{relname}")

        if not options["execute"]:
            self.stdout.write(
                self.style.WARNING(
                    "Simulacao concluida. Nenhum objeto foi removido. "
                    "Revise o projeto e a lista acima antes de usar --execute."
                )
            )
            return

        if not relations:
            self.stdout.write(self.style.WARNING("Nenhum objeto encontrado no schema public."))
            return

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(PUBLIC_RELATION_RESET_SQL)

        after_count = self.count_public_relations()
        self.stdout.write(
            self.style.SUCCESS(
                f"Reset concluido. Objetos restantes no schema public: {after_count}"
            )
        )

    def validate_safety_guards(self):
        current_environment = getattr(settings, "DJANGO_ENVIRONMENT", "")
        if current_environment != self.target_environment:
            raise CommandError(
                f"Defina DJANGO_ENVIRONMENT={self.target_environment} para executar este comando."
            )

        if settings.DEBUG:
            raise CommandError("Defina DJANGO_DEBUG=False antes de executar este comando.")

        database_url = getattr(settings, "DATABASE_URL", "")
        if not database_url:
            raise CommandError("Defina DATABASE_URL antes de executar este comando.")

        if not self.is_supabase_database_url(database_url):
            raise CommandError("DATABASE_URL deve apontar para um host Supabase.")

        confirmation = os.environ.get("SUPABASE_RESET_CONFIRM", "")
        if confirmation != self.confirmation_value:
            raise CommandError(
                f"Defina SUPABASE_RESET_CONFIRM={self.confirmation_value} para confirmar a limpeza."
            )

        if connection.vendor != "postgresql":
            raise CommandError("Este comando exige conexão PostgreSQL. SQLite foi recusado.")

        return self.validate_project_ref(database_url)

    @staticmethod
    def validate_project_ref(database_url):
        expected_ref = getattr(settings, "SUPABASE_PROJECT_REF", "").strip()
        if not expected_ref:
            raise CommandError(
                "SUPABASE_PROJECT_REF e obrigatoria para confirmar qual projeto "
                "Supabase e o alvo."
            )

        parsed = urlparse(database_url)
        hostname = (parsed.hostname or "").lower()
        username = parsed.username or ""
        direct_ref = hostname.removeprefix("db.").removesuffix(".supabase.co")
        pooler_ref = username.split(".", 1)[1] if username.startswith("postgres.") else ""
        discovered_ref = pooler_ref or direct_ref

        if discovered_ref != expected_ref:
            raise CommandError(
                "A conexao nao corresponde ao SUPABASE_PROJECT_REF esperado."
            )
        return expected_ref

    def list_public_relations(self):
        with connection.cursor() as cursor:
            cursor.execute(PUBLIC_RELATION_LIST_SQL)
            return cursor.fetchall()

    def count_public_relations(self):
        with connection.cursor() as cursor:
            cursor.execute(PUBLIC_RELATION_COUNT_SQL)
            row = cursor.fetchone()

        return row[0]

    @staticmethod
    def is_supabase_database_url(database_url):
        host = urlparse(database_url).hostname or ""
        return host.endswith(".supabase.co") or host.endswith("pooler.supabase.com")
