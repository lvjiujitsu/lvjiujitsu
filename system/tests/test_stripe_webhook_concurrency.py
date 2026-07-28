import sqlite3
import tempfile
import threading
from pathlib import Path

import stripe
from django.test import SimpleTestCase, TestCase

from system.models.registration_order import StripeWebhookEvent
from system.services.stripe_webhooks import process_stripe_event


def _build_event(event_id, event_type):
    return stripe.Event.construct_from(
        {
            "id": event_id,
            "type": event_type,
            "data": {"object": {}},
        },
        "sk_test_dummy",
    )


class SqliteDatabaseTimeoutSettingTestCase(SimpleTestCase):
    def test_local_sqlite_backend_configures_a_busy_timeout(self):
        from django.conf import settings

        db_config = settings.DATABASES["default"]
        if db_config["ENGINE"] != "django.db.backends.sqlite3":
            self.skipTest("Configuração atual não usa SQLite (Supabase HG/prod).")
        timeout = db_config.get("OPTIONS", {}).get("timeout")
        self.assertIsNotNone(
            timeout,
            "OPTIONS.timeout ausente — sem isso, escritas concorrentes no SQLite "
            "local falham imediatamente com 'database is locked' em vez de esperar.",
        )
        self.assertGreaterEqual(timeout, 10)


class SqliteBusyTimeoutMechanismTestCase(SimpleTestCase):

    def test_higher_busy_timeout_avoids_database_locked_under_concurrent_writes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "concurrency_probe.sqlite3"
            setup_conn = sqlite3.connect(str(db_path))
            setup_conn.execute("CREATE TABLE probe (id INTEGER PRIMARY KEY, value TEXT)")
            setup_conn.commit()
            setup_conn.close()

            errors = []

            def _writer(index):
                conn = sqlite3.connect(str(db_path), timeout=20)
                try:
                    conn.execute(
                        "INSERT INTO probe (value) VALUES (?)", (f"row-{index}",)
                    )
                    conn.commit()
                except sqlite3.OperationalError as exc:
                    errors.append(exc)
                finally:
                    conn.close()

            threads = [threading.Thread(target=_writer, args=(i,)) for i in range(12)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)

            self.assertEqual(errors, [])

            verify_conn = sqlite3.connect(str(db_path))
            count = verify_conn.execute("SELECT COUNT(*) FROM probe").fetchone()[0]
            verify_conn.close()
            self.assertEqual(count, 12)


class StripeWebhookDedupTestCase(TestCase):
    def test_duplicate_event_id_is_marked_duplicate_not_reprocessed(self):
        event = _build_event("evt_duplicate_1", "product.created")

        first = process_stripe_event(event)
        second = process_stripe_event(event)

        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(
            StripeWebhookEvent.objects.filter(event_id="evt_duplicate_1").count(), 1
        )
