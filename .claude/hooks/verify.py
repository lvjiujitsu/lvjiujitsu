import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    ('qualidade', ['.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py', '--all']),
)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if isinstance(payload, dict) and payload.get('stop_hook_active'):
        return 0
    failures = []
    for label, arguments in CHECKS:
        try:
            result = subprocess.run(
                [sys.executable, *arguments], cwd=ROOT, capture_output=True,
                text=True, encoding='utf-8', errors='replace', timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            failures.append(f'[{label}] verificação indisponível ou prazo esgotado.')
            continue
        if result.returncode:
            detail = (result.stderr or result.stdout).strip().splitlines()
            failures.append(f'[{label}] ' + ' | '.join(detail[-6:]))
    if not failures:
        return 0
    print('Verificação de fim de turno reprovou. Corrija antes de encerrar:', file=sys.stderr)
    for failure in failures:
        print(failure, file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
