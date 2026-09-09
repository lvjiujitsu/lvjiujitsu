from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Valida a conexão ativa sem alterar dados e sem exibir credenciais."

    def add_arguments(self, parser):
        parser.add_argument(
            "--require-postgresql",
            action="store_true",
            help="Falha se o banco ativo não for PostgreSQL.",
        )

    def handle(self, *args, **options):
        vendor = connection.vendor
        if options["require_postgresql"] and vendor != "postgresql":
            raise CommandError(
                f"PostgreSQL era obrigatório, mas o banco ativo é {vendor}."
            )

        with connection.cursor() as cursor:
            if vendor == "postgresql":
                cursor.execute(
                    """
                    SELECT current_database(),
                           current_user,
                           current_setting('server_version')
                    """
                )
                database, user, version = cursor.fetchone()
                tls_active = connection.connection.info.ssl_in_use
                if not tls_active:
                    raise CommandError(
                        "A conexão PostgreSQL respondeu, mas TLS não está ativo."
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        "Conexão PostgreSQL válida: "
                        f"database={database}; user={user}; "
                        f"server={version}; TLS=ativo."
                    )
                )
                return

            if vendor == "sqlite":
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Conexão SQLite local válida: versão={version}."
                    )
                )
                return

            cursor.execute("SELECT 1")
            cursor.fetchone()
            self.stdout.write(
                self.style.SUCCESS(f"Conexão válida: backend={vendor}.")
            )
