import logging
import warnings
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.test.runner import DiscoverRunner


logger = logging.getLogger(__name__)


class PostgreSQLDiscoverRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        static_root = Path(settings.STATIC_ROOT)
        static_root.mkdir(parents=True, exist_ok=True)

        warnings.filterwarnings(
            "ignore",
            message=r"No directory at:.*",
            category=UserWarning,
            module=r"whitenoise",
        )

        # Sem LOGGING configurado fora de produção (settings.py só define
        # LOGGING quando DEBUG=False), o handler padrão do Python escreve
        # WARNING+ direto no stderr — intercalando com os pontos de
        # progresso do unittest e quebrando a saída padronizada dos testes.
        # Mensagens de warning esperadas em branches testados (ex.:
        # notificação sem e-mail cadastrado) não são falhas; suprimir aqui
        # é o padrão documentado pelo Django para saída limpa de testes.
        # Só até WARNING — ERROR/CRITICAL continuam passando, preservando
        # `assertLogs(level="ERROR")` (ex.: test_stripe_webhook_view.py).
        logging.disable(logging.WARNING)

        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        logging.disable(logging.NOTSET)
        super().teardown_test_environment(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
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
                logger.warning(
                    "Falha ao encerrar sessões PostgreSQL antes do teardown do banco de testes.",
                    exc_info=True,
                )
            finally:
                conn.close()
        super().teardown_databases(old_config, **kwargs)
