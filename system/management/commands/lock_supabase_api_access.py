from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = (
        "Remove o acesso da Data API às tabelas Django e revoga privilégios "
        "padrão no schema public do Supabase."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Audita grants e RLS sem alterar o banco.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "Banco local não é PostgreSQL; bloqueio da Data API ignorado."
                )
            )
            return

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolname FROM pg_roles WHERE rolname IN "
                "('anon', 'authenticated', 'service_role', 'postgres', 'supabase_admin')"
            )
            roles = {row[0] for row in cursor.fetchall()}
            data_roles = [
                role
                for role in ("anon", "authenticated", "service_role")
                if role in roles
            ]
            if not data_roles:
                self.stdout.write(
                    self.style.WARNING(
                        "Papéis da Data API não existem neste PostgreSQL; nada a alterar."
                    )
                )
                return

            cursor.execute(
                """
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relkind IN ('r', 'p')
                  AND (
                    c.relname LIKE 'system\\_%' ESCAPE '\\'
                    OR c.relname LIKE 'auth\\_%' ESCAPE '\\'
                    OR c.relname LIKE 'django\\_%' ESCAPE '\\'
                  )
                ORDER BY c.relname
                """
            )
            table_names = [row[0] for row in cursor.fetchall()]
            quoted_roles = ", ".join(connection.ops.quote_name(role) for role in data_roles)

            if options["check"]:
                if table_names:
                    placeholders = ", ".join(["%s"] * len(table_names))
                    role_placeholders = ", ".join(["%s"] * len(data_roles))
                    cursor.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM information_schema.role_table_grants
                        WHERE table_schema = 'public'
                          AND table_name IN ({placeholders})
                          AND grantee IN ({role_placeholders})
                        """,
                        [*table_names, *data_roles],
                    )
                    exposed_grants = cursor.fetchone()[0]
                    cursor.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = 'public'
                          AND c.relname IN ({placeholders})
                          AND NOT c.relrowsecurity
                        """,
                        table_names,
                    )
                    without_rls = cursor.fetchone()[0]
                else:
                    exposed_grants = 0
                    without_rls = 0
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM pg_default_acl acl
                    LEFT JOIN pg_namespace namespace ON namespace.oid = acl.defaclnamespace
                    WHERE namespace.nspname = 'public'
                      AND acl.defaclacl::text ~ '(anon|authenticated|service_role)'
                    """
                )
                exposed_defaults = cursor.fetchone()[0]
                self.stdout.write(
                    "Auditoria Data API: "
                    f"tabelas_django={len(table_names)}; grants_expostos={exposed_grants}; "
                    f"sem_rls={without_rls}; defaults_expostos={exposed_defaults}."
                )
                return

            for table_name in table_names:
                quoted_table = connection.ops.quote_name(table_name)
                cursor.execute(f"ALTER TABLE {quoted_table} ENABLE ROW LEVEL SECURITY")
                cursor.execute(
                    f"REVOKE ALL PRIVILEGES ON TABLE {quoted_table} FROM {quoted_roles}"
                )

            cursor.execute(
                """
                SELECT DISTINCT sequence_ns.nspname, sequence_class.relname
                FROM pg_class sequence_class
                JOIN pg_namespace sequence_ns ON sequence_ns.oid = sequence_class.relnamespace
                JOIN pg_depend dependency ON dependency.objid = sequence_class.oid
                JOIN pg_class table_class ON table_class.oid = dependency.refobjid
                JOIN pg_namespace table_ns ON table_ns.oid = table_class.relnamespace
                WHERE sequence_class.relkind = 'S'
                  AND sequence_ns.nspname = 'public'
                  AND table_ns.nspname = 'public'
                  AND (
                    table_class.relname LIKE 'system\\_%' ESCAPE '\\'
                    OR table_class.relname LIKE 'auth\\_%' ESCAPE '\\'
                    OR table_class.relname LIKE 'django\\_%' ESCAPE '\\'
                  )
                """
            )
            for schema_name, sequence_name in cursor.fetchall():
                qualified = (
                    f"{connection.ops.quote_name(schema_name)}."
                    f"{connection.ops.quote_name(sequence_name)}"
                )
                cursor.execute(
                    f"REVOKE ALL PRIVILEGES ON SEQUENCE {qualified} FROM {quoted_roles}"
                )

            owner_roles = [role for role in ("postgres",) if role in roles]
            for owner_role in owner_roles:
                quoted_owner = connection.ops.quote_name(owner_role)
                cursor.execute(
                    f"ALTER DEFAULT PRIVILEGES FOR ROLE {quoted_owner} IN SCHEMA public "
                    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {quoted_roles}"
                )
                cursor.execute(
                    f"ALTER DEFAULT PRIVILEGES FOR ROLE {quoted_owner} IN SCHEMA public "
                    f"REVOKE USAGE, SELECT ON SEQUENCES FROM {quoted_roles}"
                )
                cursor.execute(
                    f"ALTER DEFAULT PRIVILEGES FOR ROLE {quoted_owner} IN SCHEMA public "
                    f"REVOKE EXECUTE ON FUNCTIONS FROM {quoted_roles}"
                )
                cursor.execute(
                    f"ALTER DEFAULT PRIVILEGES FOR ROLE {quoted_owner} IN SCHEMA public "
                    "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Data API bloqueada para {len(table_names)} tabela(s) Django; "
                "privilégios padrão revisados."
            )
        )
