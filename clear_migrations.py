from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

EXCLUDED_DIR_NAMES = {
    ".agents-runtime",
    ".codex-runtime",
    ".git",
    ".venv",
    "venv",
    "node_modules",
}
RUNTIME_DIR_NAMES = {
    ".codex-runtime",
    ".playwright-mcp",
    ".pytest_cache",
    ".pytest_tmp",
    "htmlcov",
    "media",
    "staticfiles",
    "test_artifacts",
    "test_screenshots",
}
RUNTIME_FILE_NAMES = {".coverage", "coverage.xml", "pytestdebug.log"}
PROJECT_PORTS = (8000,)

DATABASE_FILE_NAMES = {
    "db.sqlite3",
    "db.sqlite3-wal",
    "db.sqlite3-shm",
    "db.sqlite3-journal",
}
REMOTE_ENV_FILE_NAMES = {".env.hg", ".env.prod"}
SHARED_ENV_DIR_VARIABLE = "LVJIUJITSU_SHARED_ENV_DIR"
DEFAULT_SHARED_ENV_DIR = r"W:\Meu Drive\Desenvolvimento\lvjiujitsu"
REQUIRED_LOCAL_SEED_SETTINGS = {
    "ADMIN_SUPERUSER_USERNAME",
    "ADMIN_SUPERUSER_EMAIL",
    "ADMIN_SUPERUSER_PASSWORD",
}


class CleanupError(RuntimeError):
    pass


@dataclass(frozen=True)
class RemovalPlan:
    database: tuple[Path, ...]
    pycache: tuple[Path, ...]
    migrations: tuple[Path, ...]
    runtime: tuple[Path, ...]


def print_header(message: str) -> None:
    print()
    print(f"=== {message} ===")


def print_result(message: str) -> None:
    print(f"[OK] {message}")


def print_warning(message: str) -> None:
    print(f"[WARN] {message}")


def print_error(message: str) -> None:
    print(f"[ERRO] {message}", file=sys.stderr)


def lstat_path(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise CleanupError(f"Não foi possível inspecionar o alvo: {path}") from error


def require_lstat(path: Path) -> os.stat_result:
    path_stat = lstat_path(path)
    if path_stat is None:
        raise CleanupError(f"Alvo desapareceu durante a validação: {path}")
    return path_stat


def is_link_or_reparse_point(path: Path) -> bool:
    path_stat = require_lstat(path)
    reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(path_stat, "st_file_attributes", 0)
    return stat.S_ISLNK(path_stat.st_mode) or bool(attributes & reparse_point)


def validate_path_integrity(path: Path, root: Path) -> tuple[Path, Path]:
    lexical_root = root.absolute()
    lexical_path = path.absolute()
    try:
        relative = lexical_path.relative_to(lexical_root)
    except ValueError as error:
        raise CleanupError(f"Alvo fora do projeto recusado: {lexical_path}") from error

    current = lexical_path
    while True:
        if is_link_or_reparse_point(current):
            raise CleanupError(f"Link ou junction recusado antes da remoção: {current}")
        if current == lexical_root:
            break
        current = current.parent

    try:
        resolved_path = lexical_path.resolve()
        resolved_root = lexical_root.resolve()
        resolved_path.relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise CleanupError(f"Alvo fora do projeto recusado: {lexical_path}") from error

    return lexical_path, relative


def validate_removal_candidate(path: Path, category: str, root: Path) -> Path:
    lexical_path, relative = validate_path_integrity(path, root)
    path_stat = require_lstat(lexical_path)

    is_allowed = {
        "database": len(relative.parts) == 1
        and relative.name in DATABASE_FILE_NAMES
        and stat.S_ISREG(path_stat.st_mode),
        "runtime": len(relative.parts) == 1
        and (
            relative.name in RUNTIME_DIR_NAMES and stat.S_ISDIR(path_stat.st_mode)
            or relative.name in RUNTIME_FILE_NAMES and stat.S_ISREG(path_stat.st_mode)
        ),
        "pycache": stat.S_ISDIR(path_stat.st_mode)
        and relative.name == "__pycache__"
        and not is_excluded(lexical_path, root),
        "migration": stat.S_ISREG(path_stat.st_mode)
        and relative.name != "__init__.py"
        and relative.suffix == ".py"
        and lexical_path.parent.name == "migrations"
        and not is_excluded(lexical_path, root),
    }.get(category, False)
    if not is_allowed:
        raise CleanupError(f"Alvo não permitido para remoção: {lexical_path}")
    return lexical_path


def is_excluded(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIR_NAMES for part in relative_parts)


def remove_path(path: Path, category: str, root: Path = PROJECT_ROOT) -> bool:
    target = validate_removal_candidate(path, category, root)
    target_stat = lstat_path(target)
    if target_stat is None:
        return False

    if stat.S_ISDIR(target_stat.st_mode):
        shutil.rmtree(target, ignore_errors=True)
        return not target.exists()

    try:
        target.unlink()
        return True
    except FileNotFoundError:
        return False
    except PermissionError as error:
        os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        for _ in range(3):
            try:
                target.unlink()
                return True
            except FileNotFoundError:
                return True
            except PermissionError:
                time.sleep(0.5)
        raise CleanupError(f"Arquivo bloqueado e não removido: {target}") from error


def collect_named_paths(root: Path, names: set[str]) -> tuple[Path, ...]:
    return tuple(
        root / name
        for name in names
        if lstat_path(root / name) is not None
    )


def walk_project_paths(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    pending = [root]

    while pending:
        current = pending.pop()
        current_stat = require_lstat(current)
        if stat.S_ISLNK(current_stat.st_mode) or bool(
            getattr(current_stat, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise CleanupError(f"Link ou junction recusado antes da remoção: {current}")
        if not stat.S_ISDIR(current_stat.st_mode):
            raise CleanupError(f"Diretório inválido durante inventário: {current}")
        try:
            children = tuple(current.iterdir())
        except OSError as error:
            raise CleanupError(f"Não foi possível listar o diretório: {current}") from error
        for path in children:
            path_stat = require_lstat(path)
            if stat.S_ISLNK(path_stat.st_mode) or bool(
                getattr(path_stat, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                raise CleanupError(f"Link ou junction recusado antes da remoção: {path}")
            paths.append(path)
            if stat.S_ISDIR(path_stat.st_mode) and not is_excluded(path, root):
                pending.append(path)
    return tuple(paths)


def collect_pycache_paths(paths: tuple[Path, ...], root: Path) -> tuple[Path, ...]:
    return tuple(path for path in paths if path.name == "__pycache__" and not is_excluded(path, root))


def collect_migration_paths(paths: tuple[Path, ...], root: Path) -> tuple[Path, ...]:
    migration_dirs = {
        path
        for path in paths
        if path.name == "migrations" and not is_excluded(path, root)
    }
    return tuple(
        path
        for path in paths
        if path.parent in migration_dirs
        and path.name != "__init__.py"
        and path.suffix == ".py"
    )


def collect_runtime_paths(root: Path) -> tuple[Path, ...]:
    return collect_named_paths(root, RUNTIME_DIR_NAMES | RUNTIME_FILE_NAMES)


def build_removal_plan(root: Path = PROJECT_ROOT) -> RemovalPlan:
    project_paths = walk_project_paths(root)
    plan = RemovalPlan(
        database=collect_named_paths(root, DATABASE_FILE_NAMES),
        pycache=collect_pycache_paths(project_paths, root),
        migrations=collect_migration_paths(project_paths, root),
        runtime=collect_runtime_paths(root),
    )
    for category, paths in (
        ("database", plan.database),
        ("pycache", plan.pycache),
        ("migration", plan.migrations),
        ("runtime", plan.runtime),
    ):
        for path in paths:
            validate_removal_candidate(path, category, root)
    return plan


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
            "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | "
            "ConvertTo-Json -Compress"
        ),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, dict):
        payload = [payload]
    return payload


def build_parent_map(processes: list[dict[str, str]]) -> dict[int, int]:
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


def protected_pids(current_pid: int, parent_map: dict[int, int]) -> set[int]:
    protected = {0, current_pid}
    pid = current_pid
    while True:
        parent = parent_map.get(pid)
        if not parent or parent in protected:
            break
        protected.add(parent)
        pid = parent
    return protected


def listening_pids_on_project_ports() -> set[int]:
    if os.name != "nt":
        return set()

    ports = ",".join(str(port) for port in PROJECT_PORTS)
    command = [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        (
            "$ErrorActionPreference='SilentlyContinue'; "
            f"Get-NetTCPConnection -LocalPort {ports} -State Listen | "
            "Select-Object -ExpandProperty OwningProcess"
        ),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    pids = set()
    for line in (getattr(result, "stdout", "") or "").splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            pids.add(int(stripped))
    return pids


def process_belongs_to_repository(
    process: dict[str, str], root: Path, listening_pids: set[int] | None = None
) -> bool:
    repo_root = str(root.resolve()).rstrip("\\/").lower()
    repo_python = str((root / ".venv" / "Scripts" / "python.exe").resolve()).lower()
    executable_path = str(process.get("ExecutablePath") or "").lower()
    command_line = str(process.get("CommandLine") or "").lower()
    repo_path_markers = (f"{repo_root}\\", f"{repo_root}/")

    if executable_path == repo_python or any(
        marker in command_line for marker in repo_path_markers
    ):
        return True

    if listening_pids and "manage.py" in command_line:
        try:
            pid = int(process.get("ProcessId") or 0)
        except (TypeError, ValueError):
            return False
        return pid in listening_pids

    return False


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
        f"Timeout ({max_wait:.0f}s) - processos do projeto ainda ativos: "
        f"{', '.join(str(pid) for pid in sorted(remaining))}."
    )


def stop_python_processes(root: Path = PROJECT_ROOT) -> int:
    print_header("Encerrando processos Python do repositório")
    if os.name != "nt":
        print_warning("Enumeração de processos indisponível fora do Windows.")
        return 0

    processes = list_python_processes()
    listening = listening_pids_on_project_ports()
    protected = protected_pids(os.getpid(), build_parent_map(processes))
    stopped_pids: set[int] = set()

    for process in processes:
        try:
            pid = int(process.get("ProcessId") or 0)
        except (TypeError, ValueError):
            continue
        if pid in protected:
            continue
        if not process_belongs_to_repository(process, root, listening):
            continue

        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            stopped_pids.add(pid)
            print_result(f"Processo Python finalizado: PID {pid}")
        else:
            print_warning(f"Não foi possível finalizar o PID {pid}.")

    wait_processes_exit(stopped_pids)

    if not stopped_pids:
        print_warning("Nenhum processo Python vinculado ao repositório foi encontrado.")

    return len(stopped_pids)


def remove_database_files(
    root: Path = PROJECT_ROOT, paths: tuple[Path, ...] | None = None
) -> tuple[int, int]:
    print_header("Removendo banco SQLite")
    removed = 0
    extra_stopped = 0
    failures: list[str] = []

    paths = paths if paths is not None else build_removal_plan(root).database
    for path in paths:
        name = path.name
        try:
            if remove_path(path, "database", root):
                removed += 1
                print_result(f"Arquivo removido: {name}")
            continue
        except CleanupError:
            print_warning(
                f"Arquivo bloqueado detectado: {name}. Tentando finalizar "
                "processos Python vinculados ao repositório."
            )
            extra_stopped += stop_python_processes(root)
            try:
                if remove_path(path, "database", root):
                    removed += 1
                    print_result(f"Arquivo removido após desbloqueio: {name}")
                continue
            except CleanupError:
                failures.append(name)

    if removed == 0 and not failures:
        print_warning("Nenhum arquivo SQLite encontrado.")

    if failures:
        raise CleanupError(
            "Não foi possível remover os arquivos SQLite bloqueados: "
            f"{', '.join(failures)}. Feche o servidor Django, shells do "
            "SQLite ou processos que estejam usando o banco e execute o "
            "comando novamente."
        )

    return removed, extra_stopped


def remove_pycache_directories(
    root: Path = PROJECT_ROOT, paths: tuple[Path, ...] | None = None
) -> int:
    print_header("Removendo diretórios __pycache__")
    removed = 0

    paths = paths if paths is not None else build_removal_plan(root).pycache
    for cache_dir in paths:
        if remove_path(cache_dir, "pycache", root):
            removed += 1
            print_result(f"Diretório removido: {cache_dir.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhum diretório __pycache__ encontrado.")

    return removed


def remove_migration_files(
    root: Path = PROJECT_ROOT, paths: tuple[Path, ...] | None = None
) -> int:
    print_header("Removendo migrations do projeto")
    removed = 0

    paths = paths if paths is not None else build_removal_plan(root).migrations
    for path in paths:
        if remove_path(path, "migration", root):
            removed += 1
            print_result(f"Migration removida: {path.relative_to(root)}")

    if removed == 0:
        print_warning("Nenhuma migration adicional encontrada.")

    return removed


def remove_runtime_artifacts(
    root: Path = PROJECT_ROOT, paths: tuple[Path, ...] | None = None
) -> int:
    print_header("Removendo artefatos locais")
    removed = 0

    paths = paths if paths is not None else build_removal_plan(root).runtime
    for path in paths:
        if remove_path(path, "runtime", root):
            removed += 1
            print_result(f"Artefato removido: {path.name}")

    if removed == 0:
        print_warning("Nenhum artefato local adicional encontrado.")

    return removed


def verify_cleanup(root: Path = PROJECT_ROOT) -> None:
    remaining: list[str] = []

    for name in DATABASE_FILE_NAMES:
        if (root / name).exists():
            remaining.append(name)

    project_paths = walk_project_paths(root)
    migration_dirs = {
        path
        for path in project_paths
        if path.name == "migrations" and not is_excluded(path, root)
    }
    for path in project_paths:
        if path.parent in migration_dirs and path.name != "__init__.py":
            remaining.append(str(path.relative_to(root)))

    for name in sorted(RUNTIME_DIR_NAMES):
        if (root / name).exists():
            remaining.append(name)

    if remaining:
        raise CleanupError(
            "Limpeza incompleta; estes alvos permanecem: " + ", ".join(sorted(remaining))
        )


def validate_project(root: Path = PROJECT_ROOT) -> None:
    required = (
        root / "manage.py",
        root / "lvjiujitsu" / "settings.py",
        root / "system" / "migrations" / "__init__.py",
    )
    if any(not path.is_file() for path in required):
        raise CleanupError("O script não está na raiz válida do LV JIU JITSU.")

    environment = os.environ.get("DJANGO_ENVIRONMENT", "local").strip().lower()
    if environment in {"hg", "prod"}:
        raise CleanupError(f"Operação recusada: DJANGO_ENVIRONMENT={environment}.")


def is_path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


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


def shared_env_dir() -> Path:
    configured = os.environ.get(SHARED_ENV_DIR_VARIABLE, "").strip()
    return Path(configured or DEFAULT_SHARED_ENV_DIR)


def local_env_candidates(root: Path) -> list[Path]:
    return [root / ".env", shared_env_dir() / ".env"]


def is_allowed_env_location(env_path: Path, root: Path) -> bool:
    if is_path_within(env_path, root):
        return True
    shared = shared_env_dir()
    try:
        return is_path_within(env_path, shared.resolve())
    except OSError:
        return False


def validate_local_environment(root: Path = PROJECT_ROOT) -> Path:
    configured_env_file = os.environ.get("DJANGO_ENV_FILE", "").strip()
    if configured_env_file:
        env_path = Path(configured_env_file)
        if not env_path.is_absolute():
            env_path = root / env_path
        env_path = env_path.resolve()
    else:
        found = next(
            (path for path in local_env_candidates(root) if path.is_file()),
            None,
        )
        env_path = (found or root / ".env").resolve()

    if not is_allowed_env_location(env_path, root):
        raise CleanupError(
            "DJANGO_ENV_FILE deve apontar para um arquivo dentro do projeto ou "
            "do diretório compartilhado de ambiente."
        )
    if env_path.name.casefold() in REMOTE_ENV_FILE_NAMES:
        raise CleanupError("Ciclo destrutivo local recusado: use o arquivo .env local.")
    if not env_path.is_file():
        raise CleanupError(f"Arquivo de ambiente local não encontrado: {env_path}")

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
        os.environ.get("DATABASE_URL") or values.get("DATABASE_URL") or ""
    ).strip()
    if database_url:
        raise CleanupError(
            "Ciclo destrutivo local recusado: DATABASE_URL deve estar vazio "
            "para usar SQLite."
        )

    missing_settings = sorted(
        key
        for key in REQUIRED_LOCAL_SEED_SETTINGS
        if not (os.environ.get(key) or values.get(key) or "").strip()
    )
    if missing_settings:
        raise CleanupError(
            "Configurações obrigatórias para o ciclo completo estão vazias: "
            f"{', '.join(missing_settings)}."
        )

    return env_path


def validate_database_targets(root: Path = PROJECT_ROOT) -> None:
    resolved_root = root.resolve()
    for name in DATABASE_FILE_NAMES:
        target = (resolved_root / name).resolve()
        if target.parent != resolved_root:
            raise CleanupError(f"Alvo de banco fora da raiz do projeto: {target}")


def main() -> int:
    root = PROJECT_ROOT
    validate_project(root)
    env_path = validate_local_environment(root)
    validate_database_targets(root)
    removal_plan = build_removal_plan(root)

    print_header("Iniciando limpeza do ambiente")
    print_result(f"Repositório localizado em: {root}")
    print_result(f"Ambiente local validado: {env_path.name}")

    stopped_processes = stop_python_processes(root)
    removed_database, extra_stopped = remove_database_files(root, removal_plan.database)
    stopped_processes += extra_stopped
    removed_pycache = remove_pycache_directories(root, removal_plan.pycache)
    removed_migrations = remove_migration_files(root, removal_plan.migrations)
    removed_artifacts = remove_runtime_artifacts(root, removal_plan.runtime)

    verify_cleanup(root)

    print_header("Resumo final")
    print_result(f"Processos Python finalizados: {stopped_processes}")
    print_result(f"Arquivos SQLite removidos: {removed_database}")
    print_result(f"Diretórios __pycache__ removidos: {removed_pycache}")
    print_result(f"Migrations removidas: {removed_migrations}")
    print_result(f"Artefatos locais removidos: {removed_artifacts}")
    print_result(
        "Limpeza concluída. Agora execute makemigrations, migrate e "
        "create_admin_superuser."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CleanupError as error:
        print()
        print_error(str(error))
        raise SystemExit(1)
