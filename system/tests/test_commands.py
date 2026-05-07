import shutil
import tempfile
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command, get_commands
from django.core.management.base import CommandError, OutputWrapper
from django.test import SimpleTestCase, TestCase

from clear_migrations import remove_runtime_artifacts
from system.models import (
    BeltRank,
    ClassCategory,
    ClassGroup,
    GraduationRule,
    Holiday,
    Product,
    ProductCategory,
    ProductVariant,
    SubscriptionPlan,
    TeacherPayrollConfig,
)
from system.management.commands.inicial_seed_test import Command as InicialSeedTestCommand
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


class SeedCommandGovernanceTestCase(SimpleTestCase):
    def test_inicial_seed_command_is_not_available(self):
        get_commands.cache_clear()

        self.assertNotIn("inicial_seed", get_commands())

    def test_inicial_seed_test_runs_granular_seed_sequence(self):
        command = InicialSeedTestCommand()
        command.stdout = OutputWrapper(StringIO())

        with patch("system.management.commands.inicial_seed_test.call_command") as mocked_call:
            command.handle()

        self.assertEqual(
            [call.args[0] for call in mocked_call.call_args_list],
            [
                "seed_person_type",
                "seed_class_categories",
                "seed_ibjjf_age_categories",
                "seed_belts",
                "seed_graduation_rules",
                "seed_official_instructors",
                "seed_class_catalog",
                "seed_teacher_payroll_configs",
                "seed_product_categories",
                "seed_products",
                "seed_plans",
                "seed_holidays",
                "seed_test_personas",
                "seed_person_administrative",
            ],
        )


class SeedAuditLogCommandTestCase(TestCase):
    def _call_seed(self, command_name, **options):
        output = StringIO()
        call_command(command_name, stdout=output, **options)
        return output.getvalue()

    def test_new_granular_seed_commands_are_available(self):
        get_commands.cache_clear()
        commands = get_commands()

        self.assertIn("seed_class_categories", commands)
        self.assertIn("seed_ibjjf_age_categories", commands)
        self.assertIn("seed_graduation_rules", commands)
        self.assertIn("seed_official_instructors", commands)
        self.assertIn("seed_teacher_payroll_configs", commands)
        self.assertIn("seed_product_categories", commands)

    def test_seed_class_categories_logs_each_category(self):
        output = self._call_seed("seed_class_categories")

        self.assertEqual(ClassCategory.objects.count(), 4)
        self.assertIn("Categorias de turma cadastradas: 4", output)
        self.assertIn("- adult: Adulto | público Adulto", output)
        self.assertIn("- women: Feminino | público Feminino", output)

    def test_seed_ibjjf_age_categories_logs_each_category(self):
        output = self._call_seed("seed_ibjjf_age_categories")

        self.assertIn("Categorias etárias IBJJF cadastradas: 22", output)
        self.assertIn("- pre-mirim-1: Pré-Mirim 1 | público Kids | idade 4", output)
        self.assertIn("- master-7: Master 7 | público Adulto | idade 61+", output)

    def test_seed_belts_logs_belts_only(self):
        output = self._call_seed("seed_belts")

        self.assertEqual(BeltRank.objects.count(), 13)
        self.assertEqual(GraduationRule.objects.count(), 0)
        self.assertIn("Faixas cadastradas: 13", output)
        self.assertIn("- adult-white: Branca | público Adulto | graus 4 | próxima adult-blue", output)
        self.assertNotIn("Regras cadastradas", output)

    def test_seed_graduation_rules_requires_seed_belts_first(self):
        with self.assertRaisesMessage(CommandError, "Execute seed_belts antes de seed_graduation_rules"):
            self._call_seed("seed_graduation_rules")

    def test_seed_graduation_rules_logs_each_rule(self):
        self._call_seed("seed_belts")

        output = self._call_seed("seed_graduation_rules")

        self.assertEqual(GraduationRule.objects.count(), 52)
        self.assertIn("Regras de graduação cadastradas: 52", output)
        self.assertIn("- adult-white grau 0 -> grau 1 | meses 4 | aulas 32/12m", output)
        self.assertIn("- adult-black grau 6 -> próxima faixa | meses 84 | aulas 288/36m", output)

    def test_seed_class_catalog_logs_groups_without_payroll(self):
        self._prepare_class_catalog_dependencies()

        output = self._call_seed("seed_class_catalog")

        self.assertEqual(ClassGroup.objects.count(), 6)
        self.assertEqual(TeacherPayrollConfig.objects.count(), 0)
        self.assertIn("Turmas cadastradas: 6", output)
        self.assertIn(
            "- adult-layon: Jiu Jitsu | categoria Adulto | professor Layon Quirino | horários 5",
            output,
        )
        self.assertIn("  - monday gi 06:30", output)
        self.assertIn(
            "- women-vannessa: Jiu Jitsu | categoria Feminino | professor Vanessa Ferro | horários 1",
            output,
        )

    def test_seed_teacher_payroll_configs_logs_payroll_separately(self):
        self._prepare_class_catalog_dependencies()
        self._call_seed("seed_class_catalog")

        output = self._call_seed("seed_teacher_payroll_configs")

        self.assertEqual(TeacherPayrollConfig.objects.count(), 5)
        self.assertIn("Configurações de repasse cadastradas: 5", output)
        self.assertIn("- Layon Quirino: salário R$ 400.00 | dia 28 | regras 2", output)
        self.assertIn("- Vanessa Ferro: salário R$ 0.00 | dia 28 | regras 0", output)

    def test_seed_product_categories_logs_without_products(self):
        output = self._call_seed("seed_product_categories")

        self.assertEqual(ProductCategory.objects.count(), 4)
        self.assertEqual(Product.objects.count(), 0)
        self.assertIn("Categorias de produto cadastradas: 4", output)
        self.assertIn("- belts: Faixas", output)
        self.assertIn("- patches: Patches", output)

    def test_seed_products_requires_product_categories_first(self):
        with self.assertRaisesMessage(CommandError, "Execute seed_product_categories antes de seed_products"):
            self._call_seed("seed_products")

    def test_seed_products_logs_each_product(self):
        self._call_seed("seed_product_categories")

        output = self._call_seed("seed_products")

        self.assertEqual(Product.objects.count(), 5)
        self.assertEqual(ProductVariant.objects.count(), 62)
        self.assertIn("Produtos cadastrados: 5", output)
        self.assertIn("- belt-lv: Faixa LV | categoria Faixas | variantes 35 | estoque 70", output)
        self.assertIn("- patch-kit-3: Kit 3 Patch's Kimono | categoria Patches | variantes 1 | estoque 2", output)

    def test_seed_plans_logs_each_plan(self):
        output = self._call_seed("seed_plans")

        self.assertEqual(SubscriptionPlan.objects.count(), 64)
        self.assertIn("Planos cadastrados: 64", output)
        self.assertIn("- adult-5x-individual-monthly-pix: Plano Adulto 5x Individual Mensal PIX | R$ 257.00", output)
        self.assertIn(
            "- kids_juvenile-2x-family-monthly-credit-card: Plano Kids/Juvenil 2x Família Mensal Cartão | R$ 436.00",
            output,
        )

    def test_seed_holidays_logs_each_holiday(self):
        output = self._call_seed("seed_holidays", year=2026)

        self.assertEqual(Holiday.objects.count(), 13)
        self.assertIn("Feriados cadastrados para 2026: 13", output)
        self.assertIn("- 2026-01-01: Confraternização Universal", output)
        self.assertIn("- 2026-02-16: Carnaval", output)
        self.assertIn("- 2026-12-25: Natal", output)

    def _prepare_class_catalog_dependencies(self):
        self._call_seed("seed_person_type")
        self._call_seed("seed_class_categories")
        self._call_seed("seed_ibjjf_age_categories")
        self._call_seed("seed_belts")
        self._call_seed("seed_graduation_rules")
        self._call_seed("seed_official_instructors")
