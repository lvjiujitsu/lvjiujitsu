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
REQUIRED_LOCAL_SEED_SETTINGS = {
    "ADMIN_SUPERUSER_USERNAME",
    "ADMIN_SUPERUSER_EMAIL",
    "ADMIN_SUPERUSER_PASSWORD",
    "SEED_INITIAL_TEACHER_PASSWORD",
    "SEED_INITIAL_ADMINISTRATIVE_PASSWORD",
    "SEED_TEST_PORTAL_PASSWORD",
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


def is_path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def is_project_python_process(process: dict, root: Path) -> bool:
    executable_path = str(process.get("ExecutablePath") or "").strip()
    if executable_path and is_path_within(Path(executable_path), root):
        return True

    command_line = str(process.get("CommandLine") or "").replace("/", "\\").casefold()
    root_marker = str(root.resolve()).replace("/", "\\").casefold().rstrip("\\")
    return (
        f"{root_marker}\\" in command_line
        or f'"{root_marker}"' in command_line
        or f"'{root_marker}'" in command_line
    )


def build_parent_map(processes: list[dict]) -> dict[int, int]:
    parent_map: dict[int, int] = {}
    for process in processes:
        try:
            pid = int(process.get("ProcessId") or 0)
            ppid = int(process.get("ParentProcessId") or 0)
        except (TypeError, ValueError):
            continue
        if pid:
            parent_map[pid] = ppid
    return parent_map


def ancestor_pids(current_pid: int, parent_map: dict[int, int]) -> set[int]:
    protected = {0, current_pid}
    pid = current_pid
    while True:
        parent = parent_map.get(pid)
        if not parent or parent in protected:
            break
        protected.add(parent)
        pid = parent
    return protected


def kill_project_python_processes(root: Path) -> set[int]:
    if os.name != "nt":
        return set()

    print_header("Encerrando processos Python do projeto")
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
            "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | "
            "ConvertTo-Json -Compress"
        ),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        print_warning("Nenhum processo Python do projeto encontrado.")
        return set()

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CleanupError("Falha ao interpretar a lista de processos Python.") from exc
    if isinstance(payload, dict):
        payload = [payload]

    protected_pids = ancestor_pids(current_pid, build_parent_map(payload)) | {parent_pid}
    stopped: set[int] = set()

    for process in payload:
        pid = int(process.get("ProcessId") or 0)
        if (
            pid == 0
            or pid in protected_pids
            or not is_project_python_process(process, root)
        ):
            continue

        kill_result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if kill_result.returncode == 0:
            stopped.add(pid)
            print_result(f"Finalizado: PID {pid}")
        else:
            stderr = (kill_result.stderr or "").strip().lower()
            if "not found" in stderr or "n\xe3o" in stderr:
                print_result(f"PID {pid} ja encerrado.")
            else:
                print_warning(f"Falha ao finalizar PID {pid}.")

    if not stopped:
        print_warning("Nenhum processo Python do projeto ativo para encerrar.")

    return stopped


def wait_processes_exit(process_ids: set[int], max_wait: float = 8.0) -> None:
    if not process_ids:
        return

    print_header("Aguardando processos encerrarem")
    interval = 1.0
    elapsed = 0.0
    remaining = set(process_ids)

    while elapsed < max_wait and remaining:
        time.sleep(interval)
        elapsed += interval
        for pid in tuple(remaining):
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    (
                        "$ErrorActionPreference='SilentlyContinue'; "
                        f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) "
                        "{ exit 0 } else { exit 1 }"
                    ),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                remaining.discard(pid)
        if not remaining:
            print_result(f"Todos os processos encerrados ({elapsed:.0f}s).")
            return

    print_warning(
        f"Timeout ({max_wait:.0f}s) — processos do projeto ainda ativos: "
        f"{', '.join(str(pid) for pid in sorted(remaining))}."
    )


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
    root = root.resolve()
    if not (root / "manage.py").is_file():
        raise CleanupError("Arquivo manage.py nao encontrado ao lado do script.")
    if not (root / ".git").exists():
        raise CleanupError("Raiz Git do projeto nao encontrada ao lado do script.")


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def validate_local_environment(root: Path) -> Path:
    configured_env_file = os.environ.get("DJANGO_ENV_FILE", "").strip()
    env_path = Path(configured_env_file) if configured_env_file else root / ".env"
    if not env_path.is_absolute():
        env_path = root / env_path
    env_path = env_path.resolve()

    if not is_path_within(env_path, root):
        raise CleanupError("DJANGO_ENV_FILE deve apontar para um arquivo dentro do projeto.")
    if env_path.name.casefold() in {".env.hg", ".env.prod"}:
        raise CleanupError("Ciclo destrutivo local recusado: use o arquivo .env local.")
    if not env_path.is_file():
        raise CleanupError(f"Arquivo de ambiente local nao encontrado: {env_path}")

    values = parse_env_file(env_path)
    environment = (
        os.environ.get("DJANGO_ENVIRONMENT")
        or values.get("DJANGO_ENVIRONMENT")
        or "local"
    ).strip().lower()
    if environment != "local":
        raise CleanupError(
            "Ciclo destrutivo local recusado: DJANGO_ENVIRONMENT deve ser 'local'."
        )

    database_url = (
        os.environ.get("DATABASE_URL")
        or values.get("DATABASE_URL")
        or ""
    ).strip()
    if database_url:
        raise CleanupError(
            "Ciclo destrutivo local recusado: DATABASE_URL deve estar vazio para usar SQLite."
        )

    missing_settings = sorted(
        key
        for key in REQUIRED_LOCAL_SEED_SETTINGS
        if not (os.environ.get(key) or values.get(key) or "").strip()
    )
    if missing_settings:
        raise CleanupError(
            "Configuracoes obrigatorias para o ciclo completo estao vazias: "
            f"{', '.join(missing_settings)}."
        )

    return env_path


def validate_database_targets(root: Path) -> None:
    resolved_root = root.resolve()
    for name in DATABASE_FILE_NAMES:
        target = (resolved_root / name).resolve()
        if target.parent != resolved_root:
            raise CleanupError(f"Alvo de banco fora da raiz do projeto: {target}")


def main() -> int:
    root = Path(__file__).resolve().parent.resolve()
    validate_root(root)
    env_path = validate_local_environment(root)
    validate_database_targets(root)

    print_header("Iniciando limpeza do ambiente")
    print_result(f"Repositorio: {root}")
    print_result(f"Ambiente local validado: {env_path.name}")

    stopped = kill_project_python_processes(root)
    if stopped:
        wait_processes_exit(stopped)

    removed_db = remove_database_files(root)
    removed_cache = remove_pycache_directories(root)
    removed_migrations = remove_migration_files(root)
    removed_artifacts = remove_runtime_artifacts(root)

    verify_cleanup(root)

    print_header("Resumo final")
    print_result(f"Processos finalizados: {len(stopped)}")
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
