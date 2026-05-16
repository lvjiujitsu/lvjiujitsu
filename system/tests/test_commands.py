import shutil
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import get_commands
from django.test import SimpleTestCase

from clear_migrations import remove_runtime_artifacts


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

            with (
                patch("clear_migrations.force_remove", side_effect=capture_remove_path),
                redirect_stdout(StringIO()),
            ):
                remove_runtime_artifacts(root)

            self.assertIn(root / ".playwright-mcp", removed_paths)
            self.assertIn(root / "test_artifacts", removed_paths)
            self.assertIn(root / "test_screenshots", removed_paths)
            self.assertNotIn(root / ".venv", removed_paths)
        finally:
            shutil.rmtree(root, ignore_errors=True)


class SeedCommandGovernanceTestCase(SimpleTestCase):
    def test_inicial_seed_command_is_not_available(self):
        get_commands.cache_clear()

        self.assertNotIn("inicial_seed", get_commands())

    def test_inicial_seed_test_command_is_not_available(self):
        get_commands.cache_clear()

        self.assertNotIn("inicial_seed_test", get_commands())


