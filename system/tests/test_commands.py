import shutil
import tempfile
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command, get_commands
from django.test import SimpleTestCase, TestCase

from clear_migrations import remove_runtime_artifacts
from system.models import Holiday, TeacherPayrollConfig
from system.services.payroll_rules import decode_payroll_rules


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

    def test_single_consumer_seed_json_files_follow_command_names(self):
        data_root = Path(settings.BASE_DIR) / "static" / "initial_data"
        expected_files = (
            "seed_system_initial_belt_ranks.json",
            "seed_system_initial_class_categories.json",
            "seed_system_initial_class_catalog.json",
            "seed_system_initial_ibjjf_age_categories.json",
            "seed_system_initial_holidays.json",
            "seed_system_initial_graduation_rules.json",
            "seed_system_initial_product_categories.json",
            "seed_system_initial_product_catalog.json",
            "seed_system_initial_product_catalog_inventory.json",
            "seed_system_initial_teacher_payroll_configs.json",
            "seed_system_initial_subscription_plans.json",
        )

        missing_files = [
            filename
            for filename in expected_files
            if not (data_root / filename).exists()
        ]

        self.assertEqual(missing_files, [])


class TeacherPayrollSeedCommandTestCase(TestCase):
    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())

    def _seed_dependencies(self):
        self._call("seed_system_initial_person_type")
        self._call("seed_system_initial_belt_ranks")
        self._call("seed_system_initial_teacher")
        self._call("seed_system_initial_class_categories")
        self._call("seed_system_initial_class_categories_teacher")
        self._call("seed_system_initial_class_catalog")

    def test_seed_system_initial_teacher_payroll_configs_creates_idempotent_configs(self):
        self._seed_dependencies()

        self._call("seed_system_initial_teacher_payroll_configs")
        self._call("seed_system_initial_teacher_payroll_configs")

        self.assertEqual(TeacherPayrollConfig.objects.count(), 5)

        layon = TeacherPayrollConfig.objects.select_related("person").get(
            person__cpf="920.000.000-01"
        )
        self.assertEqual(layon.monthly_salary, Decimal("400.00"))
        self.assertEqual(layon.payment_day, 28)

        rules = decode_payroll_rules(layon.notes, strict=True)["rules"]
        self.assertEqual(len(rules), 2)
        self.assertTrue(all("class_group_id" in rule for rule in rules))
        self.assertTrue(all("class_group_code" not in rule for rule in rules))

        zero_configs = TeacherPayrollConfig.objects.filter(monthly_salary=Decimal("0.00"))
        self.assertEqual(zero_configs.count(), 3)


class HolidaySeedCommandTestCase(TestCase):
    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())

    def test_seed_system_initial_holidays_creates_idempotent_holidays(self):
        self._call("seed_system_initial_holidays")
        self._call("seed_system_initial_holidays")

        self.assertEqual(Holiday.objects.count(), 13)

        new_year = Holiday.objects.get(date="2026-01-01")
        self.assertEqual(new_year.name, "Confraternização Universal")
        self.assertTrue(new_year.is_active)

        corpus_christi = Holiday.objects.get(date="2026-06-04")
        self.assertEqual(corpus_christi.name, "Corpus Christi")


