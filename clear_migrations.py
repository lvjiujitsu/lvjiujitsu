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


def remove_path(path: Path) -> bool:
    if not path.exists():
        return False

    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return True

    try:
        path.unlink()
        return True
    except PermissionError as error:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        for _ in range(3):
            try:
                path.unlink()
                return True
            except PermissionError:
                time.sleep(0.5)
                continue
            except FileNotFoundError:
                return True
        raise CleanupError(f"Arquivo bloqueado e nao removido: {path}") from error
    except FileNotFoundError:
        return False


def list_python_processes() -> list[dict[str, str]]:
    if os.name != "nt":
        return []

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
        return []

    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        payload = [payload]
    return payload


def stop_python_processes(root: Path, match_repo_only: bool) -> int:
    scope_label = "do repositorio" if match_repo_only else "da maquina"
    print_header(f"Encerrando processos Python {scope_label}")
    current_pid = os.getpid()
    repo_root = str(root).lower()
    repo_python = str(root / ".venv" / "Scripts" / "python.exe").lower()
    stopped = 0

    for process in list_python_processes():
        pid = int(process.get("ProcessId") or 0)
        if pid == current_pid or pid == 0:
            continue

        executable_path = str(process.get("ExecutablePath") or "").lower()
        command_line = str(process.get("CommandLine") or "").lower()

        belongs_to_repo = repo_root in command_line or executable_path == repo_python
        if match_repo_only and not belongs_to_repo:
            continue

        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            stopped += 1
            print_result(f"Processo Python finalizado: PID {pid}")
        else:
            print_warning(f"Nao foi possivel finalizar o PID {pid}.")

    if stopped == 0:
        if match_repo_only:
            print_warning("Nenhum processo Python vinculado ao repositorio foi encontrado.")
        else:
            print_warning("Nenhum outro processo Python ativo foi encontrado.")

    return stopped


def remove_pycache_directories(root: Path) -> int:
    print_header("Removendo diretorios __pycache__")
    removed = 0

    for cache_dir in root.rglob("__pycache__"):
        if is_excluded(cache_dir, root):
            continue
        if remove_path(cache_dir):
            removed += 1
            print_result(f"Diretorio removido: {cache_dir.relative_to(root)}")

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
            if remove_path(path):
                removed += 1
                print_result(f"Migration removida: {path.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhuma migration adicional encontrada.")

    return removed


def remove_runtime_artifacts(root: Path) -> int:
    print_header("Removendo artefatos locais")
    removed = 0

    for name in sorted(RUNTIME_DIR_NAMES):
        path = root / name
        if remove_path(path):
            removed += 1
            print_result(f"Diretorio removido: {path.relative_to(root)}")

    for name in sorted(RUNTIME_FILE_NAMES):
        path = root / name
        if remove_path(path):
            removed += 1
            print_result(f"Arquivo removido: {path.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhum artefato local adicional encontrado.")

    return removed


def remove_database_files(root: Path) -> int:
    print_header("Removendo banco SQLite")
    removed = 0
    failures: list[Path] = []

    for name in sorted(DATABASE_FILE_NAMES):
        path = root / name
        if not path.exists():
            continue

        try:
            if remove_path(path):
                removed += 1
                print_result(f"Arquivo removido: {path.relative_to(root)}")
                continue
        except CleanupError:
            print_warning(
                f"Arquivo bloqueado detectado: {path.relative_to(root)}. "
                "Tentando finalizar processos Python vinculados ao repositorio."
            )
            stop_python_processes(root, match_repo_only=True)
            try:
                if remove_path(path):
                    removed += 1
                    print_result(f"Arquivo removido apos desbloqueio: {path.relative_to(root)}")
                    continue
            except CleanupError:
                print_warning(
                    "Bloqueio persistente. Tentando finalizar todos os outros processos Python da maquina."
                )
                stop_python_processes(root, match_repo_only=False)
                try:
                    if remove_path(path):
                        removed += 1
                        print_result(
                            f"Arquivo removido apos desbloqueio global: {path.relative_to(root)}"
                        )
                        continue
                except CleanupError:
                    failures.append(path)
                    continue

    if removed == 0 and not failures:
        print_warning("Nenhum arquivo SQLite encontrado.")

    if failures:
        failure_list = ", ".join(str(path.relative_to(root)) for path in failures)
        raise CleanupError(
            "Nao foi possivel remover os arquivos SQLite bloqueados: "
            f"{failure_list}. Feche o servidor Django, shells do SQLite ou processos que estejam "
            "usando o banco e execute o comando novamente."
        )

    return removed


def validate_root(root: Path) -> None:
    manage_py = root / "manage.py"
    if not manage_py.exists():
        raise CleanupError("Arquivo manage.py nao encontrado ao lado do script.")


def main() -> int:
    root = Path(__file__).resolve().parent
    validate_root(root)

    print_header("Iniciando limpeza do ambiente")
    print_result(f"Repositorio localizado em: {root}")

    stopped_processes = 0
    removed_database = remove_database_files(root)
    removed_pycache = remove_pycache_directories(root)
    removed_migrations = remove_migration_files(root)
    removed_runtime_artifacts = remove_runtime_artifacts(root)

    print_header("Resumo final")
    print_result(f"Processos Python finalizados: {stopped_processes}")
    print_result(f"Diretorios __pycache__ removidos: {removed_pycache}")
    print_result(f"Arquivos de migrations removidos: {removed_migrations}")
    print_result(f"Artefatos locais removidos: {removed_runtime_artifacts}")
    print_result(f"Arquivos SQLite removidos: {removed_database}")
    print_result("Limpeza concluida com sucesso.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CleanupError as error:
        print()
        print_error(str(error))
        raise SystemExit(1)
