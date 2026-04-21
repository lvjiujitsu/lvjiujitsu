from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path


EXCLUDED_DIR_NAMES = {".git", ".venv", "venv", "node_modules"}
RUNTIME_DIR_NAMES = {
    ".playwright-mcp",
    ".pytest_cache",
    ".pytest_tmp",
    "test_artifacts",
    "test_screenshots",
    "staticfiles",
    "media",
    "htmlcov",
}
RUNTIME_FILE_NAMES = {".coverage", "coverage.xml", "pytestdebug.log"}
DATABASE_FILE_NAMES = {
    "db.sqlite3",
    "db.sqlite3-shm",
    "db.sqlite3-wal",
    "db.sqlite3-journal",
}


class CleanupError(Exception):
    pass


def print_header(message: str) -> None:
    print()
    print(f"=== {message} ===")


def print_result(message: str) -> None:
    print(f"[OK] {message}")


def print_warning(message: str) -> None:
    print(f"[WARN] {message}")


def print_error(message: str) -> None:
    print(f"[ERROR] {message}")


def is_excluded(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    return any(part in EXCLUDED_DIR_NAMES for part in relative_parts)


def force_remove(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return not path.exists()
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return True
    except PermissionError:
        return False


def kill_all_python_processes() -> int:
    if os.name != "nt":
        return 0

    print_header("Encerrando todos os processos Python")
    current_pid = os.getpid()
    parent_pid = os.getppid()

    command = [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        (
            "$ErrorActionPreference='SilentlyContinue'; "
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -in @('python.exe', 'pythonw.exe', 'py.exe') } | "
            "Select-Object ProcessId,Name,ExecutablePath,CommandLine | "
            "ConvertTo-Json -Compress"
        ),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        print_warning("Nenhum processo Python encontrado.")
        return 0

    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        payload = [payload]

    protected_pids = {current_pid, parent_pid}
    stopped = 0

    for process in payload:
        pid = int(process.get("ProcessId") or 0)
        if pid == 0 or pid in protected_pids:
            continue

        kill_result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if kill_result.returncode == 0:
            stopped += 1
            print_result(f"Finalizado: PID {pid}")
        else:
            stderr = (kill_result.stderr or "").strip().lower()
            if "not found" in stderr or "n\xe3o" in stderr:
                print_result(f"PID {pid} ja encerrado.")
            else:
                print_warning(f"Falha ao finalizar PID {pid}.")

    if stopped == 0:
        print_warning("Nenhum processo Python ativo para encerrar.")

    return stopped


def wait_processes_exit(max_wait: float = 8.0) -> None:
    print_header("Aguardando processos encerrarem")
    current_pid = os.getpid()
    parent_pid = os.getppid()
    protected_pids = {current_pid, parent_pid}
    interval = 1.0
    elapsed = 0.0

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        result = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-Command",
                (
                    "$ErrorActionPreference='SilentlyContinue'; "
                    "(Get-Process -Name python,pythonw,py -ErrorAction SilentlyContinue).Count"
                ),
            ],
            capture_output=True, text=True, check=False,
        )
        count_str = (result.stdout or "").strip()
        try:
            remaining = int(count_str)
        except ValueError:
            remaining = 0

        alive_others = max(0, remaining - len(protected_pids))
        if alive_others == 0:
            print_result(f"Todos os processos encerrados ({elapsed:.0f}s).")
            return

    print_warning(f"Timeout ({max_wait:.0f}s) — alguns processos podem ainda estar ativos.")


def remove_database_files(root: Path) -> int:
    print_header("Removendo banco SQLite")
    removed = 0
    failures: list[str] = []

    for name in sorted(DATABASE_FILE_NAMES):
        path = root / name
        if not path.exists():
            continue

        for attempt in range(10):
            if force_remove(path):
                removed += 1
                print_result(f"Removido: {name}")
                break
            time.sleep(1)
        else:
            if path.exists():
                failures.append(name)
                print_error(f"Nao foi possivel remover: {name}")

    if removed == 0 and not failures:
        print_warning("Nenhum arquivo SQLite encontrado.")

    if failures:
        raise CleanupError(
            f"Arquivos SQLite bloqueados: {', '.join(failures)}. "
            "Feche todas as aplicacoes que usam o banco e tente novamente."
        )

    return removed


def remove_pycache_directories(root: Path) -> int:
    print_header("Removendo diretorios __pycache__")
    removed = 0

    for cache_dir in root.rglob("__pycache__"):
        if is_excluded(cache_dir, root):
            continue
        if force_remove(cache_dir):
            removed += 1
            print_result(f"Removido: {cache_dir.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhum diretorio __pycache__ encontrado.")

    return removed


def remove_migration_files(root: Path) -> int:
    print_header("Removendo migrations do projeto")
    removed = 0

    for migrations_dir in root.rglob("migrations"):
        if is_excluded(migrations_dir, root) or not migrations_dir.is_dir():
            continue

        for path in migrations_dir.iterdir():
            if path.name == "__init__.py":
                continue
            if force_remove(path):
                removed += 1
                print_result(f"Removido: {path.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhuma migration adicional encontrada.")

    return removed


def remove_runtime_artifacts(root: Path) -> int:
    print_header("Removendo artefatos locais")
    removed = 0

    for name in sorted(RUNTIME_DIR_NAMES):
        path = root / name
        if force_remove(path):
            removed += 1
            print_result(f"Removido: {path.relative_to(root)}")

    for name in sorted(RUNTIME_FILE_NAMES):
        path = root / name
        if force_remove(path):
            removed += 1
            print_result(f"Removido: {path.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhum artefato local adicional encontrado.")

    return removed


def verify_cleanup(root: Path) -> None:
    print_header("Verificando limpeza")
    problems: list[str] = []

    for name in sorted(DATABASE_FILE_NAMES):
        if (root / name).exists():
            problems.append(f"Banco ainda existe: {name}")

    for migrations_dir in root.rglob("migrations"):
        if is_excluded(migrations_dir, root) or not migrations_dir.is_dir():
            continue
        for path in migrations_dir.iterdir():
            if path.name != "__init__.py":
                problems.append(f"Migration restante: {path.relative_to(root)}")

    if problems:
        for problem in problems:
            print_error(problem)
        raise CleanupError("Limpeza incompleta. Veja os erros acima.")

    print_result("Ambiente limpo — banco deletado, migrations removidas.")


def validate_root(root: Path) -> None:
    manage_py = root / "manage.py"
    if not manage_py.exists():
        raise CleanupError("Arquivo manage.py nao encontrado ao lado do script.")


def main() -> int:
    root = Path(__file__).resolve().parent
    validate_root(root)

    print_header("Iniciando limpeza do ambiente")
    print_result(f"Repositorio: {root}")

    stopped = kill_all_python_processes()
    if stopped > 0:
        wait_processes_exit()

    removed_db = remove_database_files(root)
    removed_cache = remove_pycache_directories(root)
    removed_migrations = remove_migration_files(root)
    removed_artifacts = remove_runtime_artifacts(root)

    verify_cleanup(root)

    print_header("Resumo final")
    print_result(f"Processos finalizados: {stopped}")
    print_result(f"Arquivos SQLite removidos: {removed_db}")
    print_result(f"Diretorios __pycache__: {removed_cache}")
    print_result(f"Migrations removidas: {removed_migrations}")
    print_result(f"Artefatos locais: {removed_artifacts}")
    print_result("Limpeza concluida com sucesso.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CleanupError as error:
        print()
        print_error(str(error))
        raise SystemExit(1)
