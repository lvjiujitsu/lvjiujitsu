from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
MIGRATIONS_KEEP = {"__init__.py"}
CLEAN_DIRECTORIES = (
    REPO_ROOT / ".pytest_tmp",
    REPO_ROOT / "media",
    REPO_ROOT / "staticfiles",
    REPO_ROOT / "test_artifacts",
)
CLEAN_FILES = (
    REPO_ROOT / "db.sqlite3",
    REPO_ROOT / "exports" / "control" / "critical_exports.flag",
)


def main():
    print("Iniciando limpeza do workspace LV JIU JITSU...")
    removed_caches = remove_pycache(REPO_ROOT)
    removed_migrations = clean_migrations(REPO_ROOT)
    removed_paths = clean_known_paths()
    print(f"__pycache__ removidos: {removed_caches}")
    print(f"arquivos de migracao removidos: {removed_migrations}")
    print(f"artefatos adicionais removidos: {removed_paths}")
    print("Limpeza concluida.")


def remove_pycache(root: Path) -> int:
    removed = 0
    for cache_dir in root.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
            removed += 1
    return removed


def clean_migrations(root: Path) -> int:
    removed = 0
    for migrations_dir in root.rglob("migrations"):
        if ".venv" in migrations_dir.parts:
            continue
        for path in migrations_dir.iterdir():
            if path.name in MIGRATIONS_KEEP:
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            removed += 1
    return removed


def clean_known_paths() -> int:
    removed = 0
    for directory in CLEAN_DIRECTORIES:
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)
            removed += 1
    for file_path in CLEAN_FILES:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
            removed += 1
    return removed


if __name__ == "__main__":
    main()
