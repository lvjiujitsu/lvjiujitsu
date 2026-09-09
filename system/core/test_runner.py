import logging
import warnings

from django.db import connections
from django.test.runner import DiscoverRunner


logger = logging.getLogger(__name__)


class ProjectDiscoverRunner(DiscoverRunner):

    def setup_test_environment(self, **kwargs):
        warnings.filterwarnings(
            "ignore",
            message=r"No directory at:.*",
            category=UserWarning,
            module=r"whitenoise",
        )

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
