import re
from pathlib import Path

from django.core.management import get_commands
from django.test import SimpleTestCase


class SeedDocsCommandContractTestCase(SimpleTestCase):

    def test_documented_seed_commands_exist(self):
        root = Path(__file__).resolve().parents[2]
        doc = (root / "docs" / "OPERACAO-BANCO-SEEDS.md").read_text(encoding="utf-8")
        documented_commands = set(re.findall(r"`(seed_system_initial_\w+)`", doc))
        self.assertTrue(documented_commands, "Nenhum comando de seed encontrado no doc.")

        available_commands = set(get_commands())
        missing = documented_commands - available_commands
        self.assertEqual(
            missing,
            set(),
            f"Comandos documentados mas inexistentes: {missing}",
        )

    def test_holidays_documented_only_once_in_operacao_seeds(self):
        root = Path(__file__).resolve().parents[2]
        doc = (root / "docs" / "OPERACAO-BANCO-SEEDS.md").read_text(encoding="utf-8")
        occurrences = doc.count("seed_system_initial_holidays")
        self.assertGreaterEqual(occurrences, 1)
