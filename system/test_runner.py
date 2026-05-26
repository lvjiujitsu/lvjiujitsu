import warnings
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.test.runner import DiscoverRunner


class PostgreSQLDiscoverRunner(DiscoverRunner):
    """Test runner com dois ajustes para PostgreSQL via pooler (Supabase/PgBouncer):

    1. Garante que STATIC_ROOT existe antes dos testes para evitar o UserWarning
       do WhiteNoise que polui a saída dos pontos.

    2. Encerra sessões pendentes antes de deletar o banco de testes, evitando
       'database is being accessed by other users' no teardown.
    """

    def setup_test_environment(self, **kwargs):
        # Cria STATIC_ROOT se não existir (gitignored, ausente em dev)
        static_root = Path(settings.STATIC_ROOT)
        static_root.mkdir(parents=True, exist_ok=True)

        # Suprime o UserWarning do WhiteNoise caso o diretório ainda não tenha
        # sido populado por collectstatic
        warnings.filterwarnings(
            "ignore",
            message=r"No directory at:.*",
            category=UserWarning,
            module=r"whitenoise",
        )

        super().setup_test_environment(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        # Encerra sessões do pooler antes do DROP DATABASE
        for alias in connections:
            conn = connections[alias]
            if conn.vendor != "postgresql":
                continue
            try:
                test_db_name = conn.settings_dict.get("NAME", "")
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT pg_terminate_backend(pid) "
                        "FROM pg_stat_activity "
                        "WHERE datname = %s AND pid <> pg_backend_pid()",
                        [test_db_name],
                    )
            except Exception:
                pass
        super().teardown_databases(old_config, **kwargs)
