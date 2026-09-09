from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connection

def project_app_configs():
    return [
        config
        for config in apps.get_app_configs()
        if not config.name.startswith("django.")
    ]


def expected_columns_by_table():
    result = {}
    for config in project_app_configs():
        for model in config.get_models():
            table = model._meta.db_table
            result[table] = {field.column for field in model._meta.concrete_fields}
    return result


def find_schema_gaps(expected, existing_tables, columns_by_table):
    missing_tables = []
    missing_columns = []
    for table, columns in expected.items():
        if table not in existing_tables:
            missing_tables.append(table)
            continue
        actual = columns_by_table.get(table, set())
        for column in sorted(columns - actual):
            missing_columns.append((table, column))
    return missing_tables, missing_columns


class Command(BaseCommand):
    help = (
        "Compara, somente leitura, as colunas que os models do projeto "
        "esperam contra o schema real do banco conectado."
    )

    def handle(self, *args, **options):
        expected = expected_columns_by_table()

        try:
            with connection.cursor() as cursor:
                existing_tables = set(connection.introspection.table_names(cursor))
                columns_by_table = {}
                for table in expected:
                    if table in existing_tables:
                        description = connection.introspection.get_table_description(
                            cursor, table
                        )
                        columns_by_table[table] = {col.name for col in description}
        except OperationalError as exc:
            raise CommandError(
                f"Não foi possível conectar ao banco para checar o schema: {exc}"
            ) from exc

        missing_tables, missing_columns = find_schema_gaps(
            expected, existing_tables, columns_by_table
        )

        if not missing_tables and not missing_columns:
            self.stdout.write(
                self.style.SUCCESS(
                    "Schema em paridade: todas as colunas esperadas existem "
                    "no banco conectado."
                )
            )
            return

        for table in missing_tables:
            self.stderr.write(f"tabela ausente: {table}")
        for table, column in missing_columns:
            self.stderr.write(f"coluna ausente: {table}.{column}")

        detalhes = [f"tabela {t}" for t in missing_tables] + [
            f"{t}.{c}" for t, c in missing_columns
        ]
        raise CommandError(
            f"{len(missing_tables)} tabela(s) e {len(missing_columns)} "
            "coluna(s) ausentes no schema real: "
            f"{', '.join(detalhes)}. O ambiente precisa ser recriado "
            "(reset + migrate + seeds) antes deste deploy valer."
        )
