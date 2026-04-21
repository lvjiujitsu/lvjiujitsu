import shutil
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from clear_migrations import remove_runtime_artifacts
from system.management.commands.seed_holidays import (
    calculate_easter_date,
    get_brazilian_closure_dates,
)


class ClearMigrationsCleanupTestCase(SimpleTestCase):
    def test_remove_runtime_artifacts_also_removes_playwright_and_screenshot_dirs(self):
        root = Path(
            tempfile.mkdtemp(
                prefix="cleanup-artifacts-",
                dir=Path.cwd(),
            )
        )
        try:
            removed_paths = []

            def capture_remove_path(path):
                removed_paths.append(path)
                return False

            with patch("clear_migrations.force_remove", side_effect=capture_remove_path):
                remove_runtime_artifacts(root)

            self.assertIn(root / ".playwright-mcp", removed_paths)
            self.assertIn(root / "test_artifacts", removed_paths)
            self.assertIn(root / "test_screenshots", removed_paths)
            self.assertNotIn(root / ".venv", removed_paths)
        finally:
            shutil.rmtree(root, ignore_errors=True)


class SeedHolidaysCommandTestCase(SimpleTestCase):
    def test_calculates_easter_date_for_requested_year(self):
        self.assertEqual(calculate_easter_date(2026), date(2026, 4, 5))

    def test_builds_brazilian_closure_dates_for_requested_year(self):
        closure_dates = dict(get_brazilian_closure_dates(2026))

        self.assertEqual(closure_dates[date(2026, 2, 16)], "Carnaval")
        self.assertEqual(closure_dates[date(2026, 4, 3)], "Paixão de Cristo")
        self.assertEqual(closure_dates[date(2026, 6, 4)], "Corpus Christi")
        self.assertEqual(
            closure_dates[date(2026, 11, 20)],
            "Dia Nacional de Zumbi e da Consciência Negra",
        )

    def test_can_exclude_optional_closure_dates(self):
        closure_dates = dict(get_brazilian_closure_dates(2026, include_optional=False))

        self.assertNotIn(date(2026, 2, 16), closure_dates)
        self.assertNotIn(date(2026, 6, 4), closure_dates)
        self.assertIn(date(2026, 11, 20), closure_dates)
