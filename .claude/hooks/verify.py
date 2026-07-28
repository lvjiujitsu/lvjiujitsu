import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
CHECKS = (
    ("tokens CSS", [str(PYTHON), "scripts/audit_css.py"]),
    ("comentarios", [str(PYTHON), "scripts/strip_comments.py"]),
    ("contratos", [str(PYTHON), "scripts/validate_skill_frontmatter.py"]),
    ("indice de PRD", [str(PYTHON), "scripts/build_prd_index.py", "--check"]),
)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if payload.get("stop_hook_active"):
        return 0

    if not PYTHON.exists():
        return 0

    failures = []
    for label, command in CHECKS:
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode:
            detail = (result.stderr or result.stdout).strip().splitlines()
            failures.append(f"[{label}] " + " | ".join(detail[-6:]))

    if not failures:
        return 0

    print("Verificacao de fim de turno reprovou. Corrija antes de encerrar:", file=sys.stderr)
    for failure in failures:
        print(failure, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
