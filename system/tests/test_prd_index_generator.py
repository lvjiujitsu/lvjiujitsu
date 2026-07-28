from __future__ import annotations

import importlib
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

build_prd_index = importlib.import_module("build_prd_index")


INDEX_TEMPLATE = """# Indice de PRDs

Cabecalho que o gerador precisa preservar.

## Tabela completa

{table}
## Notas

- Nota que o gerador precisa preservar.
"""

PRD_BODY = """# PRD-{number}: {title}

## Final status

{status}
"""


class PrdIndexGeneratorTests(SimpleTestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.prd_dir = self.root / "docs" / "prd"
        self.prd_dir.mkdir(parents=True)
        self.index = self.prd_dir / "README.md"

        patcher = mock.patch.multiple(
            build_prd_index, PRD_DIR=self.prd_dir, INDEX=self.index
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_prd(self, number: str, title: str, status: str = "Concluída.") -> None:
        self.write_prd_as(f"PRD-{number}-slug-do-arquivo.md", number, title, status)

    def write_prd_as(
        self, filename: str, number: str, title: str, status: str = "Concluída."
    ) -> None:
        (self.prd_dir / filename).write_text(
            PRD_BODY.format(number=number, title=title, status=status),
            encoding="utf-8",
        )

    def write_index(self, table: str = "") -> None:
        self.index.write_text(INDEX_TEMPLATE.format(table=table), encoding="utf-8")

    def test_all_prds_are_listed_in_number_order(self) -> None:
        self.write_prd("002", "Segunda")
        self.write_prd("001", "Primeira")
        self.write_index()

        rendered = build_prd_index.render_index()

        self.assertLess(rendered.index("| 001 |"), rendered.index("| 002 |"))

    def test_header_and_notes_are_preserved(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_index()

        rendered = build_prd_index.render_index()

        self.assertIn("Cabecalho que o gerador precisa preservar.", rendered)
        self.assertIn("Nota que o gerador precisa preservar.", rendered)

    def test_next_free_number_keeps_three_digits(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_prd("017", "Seventeen")
        self.write_index()

        self.assertIn("**Próximo número livre: 018**", build_prd_index.render_index())

    def test_status_comes_from_final_status_section(self) -> None:
        self.write_prd("001", "Primeira", status="Concluída com limitações.")
        self.write_index()

        self.assertIn("concluída com limitações", build_prd_index.render_index())

    def test_prd_without_status_section_is_marked_unknown(self) -> None:
        (self.prd_dir / "PRD-001-sem-status.md").write_text(
            "# PRD-001: Sem status\n", encoding="utf-8"
        )
        self.write_index()

        self.assertIn("| — |", build_prd_index.render_index())

    def test_prd_without_heading_makes_generator_fail(self) -> None:
        (self.prd_dir / "PRD-001-sem-cabecalho.md").write_text(
            "Corpo sem cabecalho reconhecido.\n", encoding="utf-8"
        )
        self.write_index()

        with self.assertRaises(build_prd_index.IndexError_) as raised:
            build_prd_index.render_index()

        self.assertIn("cabecalho", str(raised.exception))

    def test_em_dash_separator_is_accepted(self) -> None:
        (self.prd_dir / "PRD-001-com-em-dash.md").write_text(
            "# PRD-001 — Titulo com em-dash\n", encoding="utf-8"
        )
        self.write_index()

        self.assertIn("Titulo com em-dash", build_prd_index.render_index())

    def test_file_outside_naming_pattern_makes_generator_fail(self) -> None:
        self.write_prd("001", "Primeira")
        (self.prd_dir / "AUDIT-alguma-coisa.md").write_text("# x\n", encoding="utf-8")
        self.write_index()

        with self.assertRaises(build_prd_index.IndexError_) as raised:
            build_prd_index.render_index()

        self.assertIn("fora do padrao", str(raised.exception))

    def test_duplicate_number_makes_generator_fail(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_prd_as("PRD-001-outro-slug.md", "001", "Colidente")
        self.write_index()

        with self.assertRaises(build_prd_index.IndexError_) as raised:
            build_prd_index.render_index()

        message = str(raised.exception)
        self.assertIn("duplicado", message)
        self.assertIn("PRD-001", message)
        self.assertIn("PRD-001-outro-slug.md", message)

    def test_missing_anchor_makes_generator_fail(self) -> None:
        self.write_prd("001", "Primeira")
        self.index.write_text("# Indice sem ancora\n", encoding="utf-8")

        with self.assertRaises(build_prd_index.IndexError_):
            build_prd_index.render_index()


class PrdIndexCheckModeTests(PrdIndexGeneratorTests):
    def test_check_fails_when_index_is_stale(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_index()

        with mock.patch.object(sys, "argv", ["build_prd_index.py", "--check"]):
            self.assertEqual(build_prd_index.main(), 1)

    def test_check_does_not_write_the_file(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_index()
        before = self.index.read_text(encoding="utf-8")

        with mock.patch.object(sys, "argv", ["build_prd_index.py", "--check"]):
            build_prd_index.main()

        self.assertEqual(self.index.read_text(encoding="utf-8"), before)

    def test_check_passes_after_regeneration(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_index()

        with mock.patch.object(sys, "argv", ["build_prd_index.py"]):
            self.assertEqual(build_prd_index.main(), 0)
        with mock.patch.object(sys, "argv", ["build_prd_index.py", "--check"]):
            self.assertEqual(build_prd_index.main(), 0)

    def test_check_fails_when_a_number_is_duplicated(self) -> None:
        self.write_prd("001", "Primeira")
        self.write_prd_as("PRD-001-outro-slug.md", "001", "Colidente")
        self.write_index()

        with mock.patch.object(sys, "argv", ["build_prd_index.py", "--check"]):
            self.assertEqual(build_prd_index.main(), 1)
