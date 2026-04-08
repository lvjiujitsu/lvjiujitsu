import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

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

            with patch("clear_migrations.remove_path", side_effect=capture_remove_path):
                remove_runtime_artifacts(root)

            self.assertIn(root / ".playwright-mcp", removed_paths)
            self.assertIn(root / "test_artifacts", removed_paths)
            self.assertIn(root / "test_screenshots", removed_paths)
            self.assertNotIn(root / ".venv", removed_paths)
        finally:
            shutil.rmtree(root, ignore_errors=True)
