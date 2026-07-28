
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRD_DIR = ROOT / "docs" / "prd"
INDEX = PRD_DIR / "README.md"

TABLE_HEADING = "## Tabela completa"
STATUS_HEADING = "## Final status"
FILENAME_PATTERN = re.compile(r"^PRD-(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")

KNOWN_EXCEPTIONS = {"README.md"}

STATUS_PATTERNS = (
    ("não iniciada", "não iniciada"),
    ("nao iniciada", "não iniciada"),
    ("não concluída", "não concluída"),
    ("nao concluida", "não concluída"),
    ("concluída com limitaç", "concluída com limitações"),
    ("concluida com limitac", "concluída com limitações"),
    ("em andamento", "em andamento"),
    ("registrada para decisão posterior", "registrada para decisão"),
    ("superada", "superada"),
    ("concluída", "concluída"),
    ("concluida", "concluída"),
)


class IndexError_(RuntimeError):
    pass


def extract_status(text: str) -> str:
    match = re.search(
        rf"^{re.escape(STATUS_HEADING)}\s*$(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return "—"

    body = match.group(1).strip()
    if not body:
        return "—"

    probe = body.lower()[:400]
    for needle, label in STATUS_PATTERNS:
        if needle in probe:
            return label
    return "—"


def extract_title(text: str, path: Path) -> str:
    match = re.search(r"^#\s*PRD-\d+\s*[:\-–—]\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        raise IndexError_(
            f"{path.name} nao tem cabecalho '# PRD-<NNN>: <titulo>'. "
            "Sem ele o indice inventaria um titulo."
        )
    return match.group(1).strip()


def collect_prd_files() -> list[Path]:
    unexpected = [
        path.name
        for path in sorted(PRD_DIR.glob("*.md"))
        if path.name not in KNOWN_EXCEPTIONS and not FILENAME_PATTERN.match(path.name)
    ]
    if unexpected:
        raise IndexError_(
            "Arquivo em docs/prd/ fora do padrao PRD-<NNN>-<slug>.md: "
            + ", ".join(unexpected)
        )

    prd_files = sorted(PRD_DIR.glob("PRD-*.md"))
    if not prd_files:
        raise IndexError_("Nenhuma PRD encontrada em docs/prd/.")

    by_number: dict[str, list[str]] = {}
    for path in prd_files:
        number = FILENAME_PATTERN.match(path.name).group(1)
        by_number.setdefault(number, []).append(path.name)

    duplicated = {
        number: names for number, names in by_number.items() if len(names) > 1
    }
    if duplicated:
        detail = "; ".join(
            f"PRD-{number}: {', '.join(sorted(names))}"
            for number, names in sorted(duplicated.items())
        )
        raise IndexError_(
            "Numero de PRD duplicado em docs/prd/. O indice e a fonte do proximo "
            f"numero livre e nao pode conter colisao: {detail}"
        )
    return prd_files


def render_index() -> str:
    prd_files = collect_prd_files()

    rows = []
    for path in prd_files:
        text = path.read_text(encoding="utf-8")
        number = FILENAME_PATTERN.match(path.name).group(1)
        rows.append(
            f"| {number} | {extract_title(text, path)} | {extract_status(text)} "
            f"| [{path.name}]({path.name}) |"
        )

    highest = max(int(FILENAME_PATTERN.match(p.name).group(1)) for p in prd_files)
    next_free = f"{highest + 1:03d}"

    index_text = INDEX.read_text(encoding="utf-8")
    head, separator, remainder = index_text.partition(TABLE_HEADING)
    if not separator:
        raise IndexError_(f"Ancora '{TABLE_HEADING}' nao encontrada em {INDEX}.")

    tail_match = re.search(r"^## .*", remainder, flags=re.MULTILINE)
    tail = "\n" + remainder[tail_match.start():] if tail_match else ""

    table = "\n".join(
        [
            separator,
            "",
            f"**Próximo número livre: {next_free}**",
            "",
            "Status extraído da seção `## Final status` de cada arquivo, nunca",
            "digitado à mão. Regenerar com `python scripts/build_prd_index.py`.",
            "",
            "| N | Título | Status | Arquivo |",
            "|---:|---|---|---|",
            *rows,
            "",
        ]
    )
    return head + table + tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Falha se o indice em disco estiver defasado. Nao escreve nada.",
    )
    args = parser.parse_args()

    try:
        rendered = render_index()
    except IndexError_ as error:
        print(f"[ERRO] {error}", file=sys.stderr)
        return 1

    current = INDEX.read_text(encoding="utf-8")
    if args.check:
        if current != rendered:
            print(
                "[ERRO] docs/prd/README.md esta defasado. "
                "Rode `python scripts/build_prd_index.py` e inclua o resultado "
                "no mesmo commit da PRD.",
                file=sys.stderr,
            )
            return 1
        print("Indice em dia.")
        return 0

    INDEX.write_text(rendered, encoding="utf-8", newline="\n")
    total = rendered.count("\n| ") - 1
    print(f"{total} PRD(s) indexada(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
