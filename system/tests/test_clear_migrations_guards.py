
from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

clear_migrations = importlib.import_module("clear_migrations")


LOCAL_ENV_CONTENT = "\n".join(
    [
        "DJANGO_ENVIRONMENT=local",
        "DATABASE_URL=",
        "ADMIN_SUPERUSER_USERNAME=admin",
        "ADMIN_SUPERUSER_EMAIL=admin@example.com",
        "ADMIN_SUPERUSER_PASSWORD=troque-me",
        "SEED_INITIAL_TEACHER_PASSWORD=fixture",
        "SEED_INITIAL_ADMINISTRATIVE_PASSWORD=fixture",
    ]
)

CLEARED_ENVIRONMENT = {
    key: ""
    for key in (
        "DJANGO_ENV_FILE",
        "DJANGO_ENVIRONMENT",
        "DATABASE_URL",
        *clear_migrations.REQUIRED_LOCAL_SEED_SETTINGS,
    )
}


class ClearMigrationsGuardTests(SimpleTestCase):

    def setUp(self) -> None:
        self.root = self.make_temp_dir()
        (self.root / "manage.py").write_text("", encoding="utf-8")
        self.database = self.root / "db.sqlite3"
        self.database.write_text("conteudo", encoding="utf-8")
        self.env_file = self.root / ".env"
        self.env_file.write_text(LOCAL_ENV_CONTENT, encoding="utf-8")
        self.shared = self.make_temp_dir()

    def make_temp_dir(self) -> Path:
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        return Path(directory)

    def _validate(self, **overrides: str) -> Path:
        environment = {
            **CLEARED_ENVIRONMENT,
            "LVJIUJITSU_SHARED_ENV_DIR": str(self.shared),
            **overrides,
        }
        with mock.patch.dict(os.environ, environment, clear=False):
            return clear_migrations.validate_local_environment(self.root)

    def assertRefused(self, expected_fragment: str, **overrides: str) -> None:
        with self.assertRaises(RuntimeError) as raised:
            self._validate(**overrides)

        self.assertIn(expected_fragment, str(raised.exception))
        self.assertTrue(
            self.database.is_file(),
            "O banco local não pode ser removido no caminho de recusa.",
        )

    def test_local_env_file_is_accepted(self) -> None:
        self.assertEqual(self._validate(), self.env_file.resolve())

    def test_env_file_outside_project_is_refused(self) -> None:
        outside = self.make_temp_dir() / ".env"
        outside.write_text(LOCAL_ENV_CONTENT, encoding="utf-8")

        self.assertRefused("dentro do projeto", DJANGO_ENV_FILE=str(outside))

    def test_homologation_env_file_name_is_refused(self) -> None:
        homologation = self.root / ".env.hg"
        homologation.write_text(LOCAL_ENV_CONTENT, encoding="utf-8")

        self.assertRefused("arquivo .env local", DJANGO_ENV_FILE=str(homologation))

    def test_production_env_file_name_is_refused(self) -> None:
        production = self.root / ".env.prod"
        production.write_text(LOCAL_ENV_CONTENT, encoding="utf-8")

        self.assertRefused("arquivo .env local", DJANGO_ENV_FILE=str(production))

    def test_missing_env_file_is_refused(self) -> None:
        self.env_file.unlink()

        self.assertRefused("não encontrado")

    def test_env_file_in_the_shared_directory_is_accepted(self) -> None:
        self.env_file.unlink()
        shared_env = self.shared / ".env"
        shared_env.write_text(LOCAL_ENV_CONTENT, encoding="utf-8")

        self.assertEqual(self._validate(), shared_env.resolve())

    def test_remote_environment_is_refused(self) -> None:
        self.assertRefused("DJANGO_ENVIRONMENT", DJANGO_ENVIRONMENT="prod")

    def test_remote_environment_declared_in_file_is_refused(self) -> None:
        self.env_file.write_text(
            LOCAL_ENV_CONTENT.replace(
                "DJANGO_ENVIRONMENT=local", "DJANGO_ENVIRONMENT=hg"
            ),
            encoding="utf-8",
        )

        self.assertRefused("DJANGO_ENVIRONMENT")

    def test_filled_database_url_is_refused(self) -> None:
        self.assertRefused(
            "DATABASE_URL",
            DATABASE_URL="postgresql://user:secret@db.example.supabase.co:5432/postgres",
        )

    def test_missing_seed_setting_is_refused(self) -> None:
        self.env_file.write_text(
            LOCAL_ENV_CONTENT.replace(
                "ADMIN_SUPERUSER_PASSWORD=troque-me", "ADMIN_SUPERUSER_PASSWORD="
            ),
            encoding="utf-8",
        )

        self.assertRefused("ADMIN_SUPERUSER_PASSWORD")

    def test_process_environment_overrides_env_file(self) -> None:
        self.assertRefused("DJANGO_ENVIRONMENT", DJANGO_ENVIRONMENT="hg")


class CleanupVerificationTests(SimpleTestCase):

    def setUp(self) -> None:
        self.root = self.make_temp_dir()
        self.migrations = self.root / "system" / "migrations"
        self.migrations.mkdir(parents=True)
        (self.migrations / "__init__.py").write_text("", encoding="utf-8")

    def make_temp_dir(self) -> Path:
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        return Path(directory)

    def test_clean_tree_passes(self) -> None:
        clear_migrations.verify_cleanup(self.root)

    def test_remaining_database_is_refused(self) -> None:
        (self.root / "db.sqlite3").write_text("conteudo", encoding="utf-8")

        with self.assertRaises(clear_migrations.CleanupError) as raised:
            clear_migrations.verify_cleanup(self.root)

        self.assertIn("db.sqlite3", str(raised.exception))

    def test_remaining_migration_is_refused(self) -> None:
        (self.migrations / "0001_initial.py").write_text("", encoding="utf-8")

        with self.assertRaises(clear_migrations.CleanupError) as raised:
            clear_migrations.verify_cleanup(self.root)

        self.assertIn("0001_initial.py", str(raised.exception))

    def test_runtime_worktree_migration_is_not_a_cleanup_remnant(self) -> None:
        migration = (
            self.root
            / ".agents-runtime"
            / "worktrees"
            / "feature"
            / "system"
            / "migrations"
            / "0001_initial.py"
        )
        migration.parent.mkdir(parents=True)
        migration.write_text("", encoding="utf-8")

        clear_migrations.verify_cleanup(self.root)
        self.assertTrue(migration.is_file())

    def test_verify_cleanup_prunes_runtime_before_enumerating_descendants(self) -> None:
        runtime = self.root / ".agents-runtime"
        migration = (
            runtime
            / "worktrees"
            / "feature"
            / "system"
            / "migrations"
            / "0001_initial.py"
        )
        migration.parent.mkdir(parents=True)
        migration.write_text("", encoding="utf-8")
        original_iterdir = Path.iterdir

        def guarded_iterdir(path: Path):
            if path == runtime:
                self.fail("A verificação não pode enumerar .agents-runtime.")
            return original_iterdir(path)

        with (
            mock.patch.object(Path, "iterdir", new=guarded_iterdir),
            mock.patch.object(
                Path,
                "rglob",
                side_effect=AssertionError("A verificação não pode usar rglob."),
            ) as rglob,
        ):
            clear_migrations.verify_cleanup(self.root)

        rglob.assert_not_called()
        self.assertTrue(migration.is_file())

    def test_init_file_alone_is_not_a_remnant(self) -> None:
        clear_migrations.verify_cleanup(self.root)

    def test_remaining_runtime_directory_is_refused(self) -> None:
        (self.root / "staticfiles").mkdir()

        with self.assertRaises(clear_migrations.CleanupError) as raised:
            clear_migrations.verify_cleanup(self.root)

        self.assertIn("staticfiles", str(raised.exception))

    def test_remaining_legacy_codex_runtime_directory_is_refused(self) -> None:
        (self.root / ".codex-runtime").mkdir()

        with self.assertRaises(clear_migrations.CleanupError) as raised:
            clear_migrations.verify_cleanup(self.root)

        self.assertIn(".codex-runtime", str(raised.exception))

    def test_cleanup_error_is_a_runtime_error(self) -> None:
        self.assertTrue(issubclass(clear_migrations.CleanupError, RuntimeError))


class ProcessFilterTests(SimpleTestCase):

    def test_process_from_project_venv_is_accepted(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        executable = (root / ".venv" / "Scripts" / "python.exe").resolve()

        self.assertTrue(
            clear_migrations.process_belongs_to_repository(
                {"ExecutablePath": str(executable), "CommandLine": ""}, root
            )
        )

    def test_process_with_project_path_in_command_line_is_accepted(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        command_line = f"python {root}\\manage.py runserver"

        self.assertTrue(
            clear_migrations.process_belongs_to_repository(
                {"ExecutablePath": "C:\\Python312\\python.exe", "CommandLine": command_line},
                root,
            )
        )

    def test_ancestors_are_protected_from_being_killed(self) -> None:
        parent_map = {4242: 1010, 1010: 500, 500: 0}

        protected = clear_migrations.protected_pids(4242, parent_map)

        self.assertIn(4242, protected)
        self.assertIn(1010, protected)
        self.assertIn(500, protected)

    def test_protected_pids_survives_parent_cycle(self) -> None:
        parent_map = {10: 20, 20: 10}

        protected = clear_migrations.protected_pids(10, parent_map)

        self.assertEqual(protected, {0, 10, 20})

    def test_build_parent_map_ignores_malformed_entries(self) -> None:
        parent_map = clear_migrations.build_parent_map(
            [
                {"ProcessId": "10", "ParentProcessId": "4"},
                {"ProcessId": None, "ParentProcessId": "4"},
                {"ProcessId": "abc", "ParentProcessId": "4"},
            ]
        )

        self.assertEqual(parent_map, {10: 4})

    def test_sibling_process_is_not_protected(self) -> None:
        parent_map = {4242: 1010, 1010: 500, 500: 0, 7777: 500}

        protected = clear_migrations.protected_pids(4242, parent_map)

        self.assertNotIn(7777, protected)

    def test_unrelated_python_process_is_rejected(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)

        self.assertFalse(
            clear_migrations.process_belongs_to_repository(
                {
                    "ExecutablePath": "C:\\Python312\\python.exe",
                    "CommandLine": "python C:\\outro\\manage.py runserver",
                },
                root,
            )
        )


class ContainmentTests(SimpleTestCase):

    def test_target_outside_project_is_refused(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, True)
        victim = outside / "arquivo.txt"
        victim.write_text("conteudo", encoding="utf-8")

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.remove_path(victim, "runtime", root)

        self.assertTrue(victim.is_file(), "Arquivo fora do projeto não pode ser tocado.")

    def test_excluded_directories_are_skipped(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        vendored = root / ".venv" / "lib" / "__pycache__"
        vendored.mkdir(parents=True)

        self.assertTrue(clear_migrations.is_excluded(vendored, root))


class RemovalPreflightTests(SimpleTestCase):

    def create_symbolic_directory_link(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Link simbólico indisponível neste Windows: {error}")

    def create_directory_link(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
            return
        except OSError as error:
            result = subprocess.run(
                [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(link),
                    str(target),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                self.skipTest(
                    f"Link e junction indisponíveis neste Windows: {error}; "
                    f"{result.stderr.strip()}"
                )

    def test_regular_runtime_target_is_removed(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        runtime = root / "media"
        runtime.mkdir()
        marker = runtime / "marker.txt"
        marker.write_text("runtime", encoding="utf-8")

        removed = clear_migrations.remove_runtime_artifacts(root)

        self.assertEqual(removed, 1)
        self.assertFalse(runtime.exists())

    def test_legacy_codex_runtime_directory_is_removed_as_runtime_residue(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        legacy = root / ".codex-runtime" / "worktrees" / "issue-11-example"
        legacy.mkdir(parents=True)
        (legacy / "db.sqlite3").write_text("", encoding="utf-8")

        removed = clear_migrations.remove_runtime_artifacts(root)

        self.assertEqual(removed, 1)
        self.assertFalse((root / ".codex-runtime").exists())

    def test_internal_path_outside_runtime_allowlist_is_refused(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        source = root / "system"
        source.mkdir()
        marker = source / "module.py"
        marker.write_text("source", encoding="utf-8")

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.remove_path(source, "runtime", root)

        self.assertTrue(source.is_dir())
        self.assertTrue(marker.is_file())

    def test_lstat_error_is_refused_before_removal(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        runtime = root / "media"
        runtime.mkdir()

        with mock.patch.object(Path, "lstat", side_effect=OSError("falha")):
            with self.assertRaises(clear_migrations.CleanupError):
                clear_migrations.remove_path(runtime, "runtime", root)

        self.assertTrue(runtime.is_dir())

    def test_linked_ancestor_is_refused_before_removal(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        target = root / "target"
        cache = target / "__pycache__"
        cache.mkdir(parents=True)
        marker = cache / "module.pyc"
        marker.write_text("cache", encoding="utf-8")
        linked_parent = root / "linked"
        self.create_directory_link(linked_parent, target)

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.remove_path(
                linked_parent / "__pycache__", "pycache", root
            )

        self.assertTrue(cache.is_dir())
        self.assertTrue(marker.is_file())

    def test_broken_directory_link_is_refused_before_removal(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        target = root / "target"
        target.mkdir()
        runtime_link = root / "staticfiles"
        self.create_directory_link(runtime_link, target)
        shutil.rmtree(target)

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.remove_path(runtime_link, "runtime", root)

        self.assertTrue(runtime_link.is_symlink() or not runtime_link.exists())

    def test_build_plan_refuses_database_directory(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        database_directory = root / "db.sqlite3"
        database_directory.mkdir()

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.build_removal_plan(root)

        self.assertTrue(database_directory.is_dir())

    def test_build_plan_refuses_pycache_file(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        cache_file = root / "__pycache__"
        cache_file.write_text("not a directory", encoding="utf-8")

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.build_removal_plan(root)

        self.assertTrue(cache_file.is_file())

    def test_main_preflight_refuses_broken_runtime_junction_before_mutation(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        (root / "manage.py").write_text("", encoding="utf-8")
        (root / "lvjiujitsu").mkdir()
        (root / "lvjiujitsu" / "settings.py").write_text("", encoding="utf-8")
        migrations = root / "system" / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "__init__.py").write_text("", encoding="utf-8")
        (root / ".env").write_text(LOCAL_ENV_CONTENT, encoding="utf-8")
        media = root / "media"
        media.mkdir()
        target = root / "target"
        target.mkdir()
        runtime_link = root / "staticfiles"
        self.create_directory_link(runtime_link, target)
        shutil.rmtree(target)

        with mock.patch.object(clear_migrations, "PROJECT_ROOT", root):
            with self.assertRaises(clear_migrations.CleanupError):
                clear_migrations.main()

        self.assertTrue(media.is_dir())

    def test_main_preflight_refuses_metadata_error_before_mutation(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        (root / "manage.py").write_text("", encoding="utf-8")
        (root / "lvjiujitsu").mkdir()
        (root / "lvjiujitsu" / "settings.py").write_text("", encoding="utf-8")
        migrations = root / "system" / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "__init__.py").write_text("", encoding="utf-8")
        (root / ".env").write_text(LOCAL_ENV_CONTENT, encoding="utf-8")
        media = root / "media"
        media.mkdir()

        with mock.patch.object(Path, "lstat", side_effect=OSError("falha")):
            with mock.patch.object(clear_migrations, "PROJECT_ROOT", root):
                with self.assertRaises(clear_migrations.CleanupError):
                    clear_migrations.main()

        self.assertTrue(media.is_dir())

    def test_migrations_and_pycache_are_removed_from_normal_tree(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        migrations = root / "system" / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "__init__.py").write_text("", encoding="utf-8")
        migration = migrations / "0001_initial.py"
        migration.write_text("migration", encoding="utf-8")
        cache = migrations / "__pycache__"
        cache.mkdir()
        (cache / "0001_initial.pyc").write_text("cache", encoding="utf-8")

        plan = clear_migrations.build_removal_plan(root)
        clear_migrations.remove_pycache_directories(root, plan.pycache)
        clear_migrations.remove_migration_files(root, plan.migrations)
        clear_migrations.verify_cleanup(root)

        self.assertFalse(migration.exists())
        self.assertFalse(cache.exists())

    def test_runtime_worktree_migrations_are_excluded_from_removal_plan(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        migrations = root / "system" / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "__init__.py").write_text("", encoding="utf-8")
        target_migration = migrations / "0001_initial.py"
        target_migration.write_text("migration", encoding="utf-8")
        runtime_migration = (
            root
            / ".agents-runtime"
            / "worktrees"
            / "feature"
            / "system"
            / "migrations"
            / "0001_initial.py"
        )
        runtime_migration.parent.mkdir(parents=True)
        runtime_migration.write_text("migration", encoding="utf-8")

        plan = clear_migrations.build_removal_plan(root)

        self.assertEqual(plan.migrations, (target_migration,))
        clear_migrations.remove_migration_files(root, plan.migrations)
        clear_migrations.verify_cleanup(root)
        self.assertFalse(target_migration.exists())
        self.assertTrue(runtime_migration.is_file())

    def test_main_preflight_preserves_all_targets_when_runtime_link_is_unsafe(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        (root / "manage.py").write_text("", encoding="utf-8")
        (root / "lvjiujitsu").mkdir()
        (root / "lvjiujitsu" / "settings.py").write_text("", encoding="utf-8")
        migrations = root / "system" / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "__init__.py").write_text("", encoding="utf-8")
        (root / ".env").write_text(LOCAL_ENV_CONTENT, encoding="utf-8")
        media = root / "media"
        media.mkdir()
        victim = root / "system" / "source"
        victim.mkdir()
        runtime_link = root / "staticfiles"
        self.create_directory_link(runtime_link, victim)

        with mock.patch.object(clear_migrations, "PROJECT_ROOT", root):
            with self.assertRaises(clear_migrations.CleanupError):
                clear_migrations.main()

        self.assertTrue(media.is_dir())
        self.assertTrue(victim.is_dir())
        self.assertTrue(runtime_link.exists())

    def test_runtime_link_to_internal_non_target_refuses_before_any_removal(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        valid_runtime = root / "media"
        valid_runtime.mkdir()
        valid_marker = valid_runtime / "valid.txt"
        valid_marker.write_text("valid", encoding="utf-8")
        internal_victim = root / "system"
        internal_victim.mkdir()
        victim_marker = internal_victim / "victim.txt"
        victim_marker.write_text("victim", encoding="utf-8")
        runtime_link = root / "staticfiles"

        self.create_directory_link(runtime_link, internal_victim)

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.remove_runtime_artifacts(root)

        self.assertTrue(valid_runtime.is_dir())
        self.assertTrue(valid_marker.is_file())
        self.assertTrue(runtime_link.exists())
        self.assertTrue(internal_victim.is_dir())
        self.assertTrue(victim_marker.is_file())

    def test_real_symbolic_runtime_link_is_preserved_with_its_victim(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        victim = root / "system"
        victim.mkdir()
        marker = victim / "module.py"
        marker.write_text("source", encoding="utf-8")
        runtime_link = root / "staticfiles"
        self.create_symbolic_directory_link(runtime_link, victim)

        with self.assertRaises(clear_migrations.CleanupError):
            clear_migrations.remove_runtime_artifacts(root)

        self.assertTrue(runtime_link.is_symlink())
        self.assertTrue(victim.is_dir())
        self.assertTrue(marker.is_file())

    def test_cache_and_migration_discovery_refuse_links(self) -> None:
        for directory_name in ("__pycache__", "migrations"):
            with self.subTest(directory_name=directory_name):
                root = Path(tempfile.mkdtemp())
                self.addCleanup(shutil.rmtree, root, True)
                victim = root / "protected"
                victim.mkdir()
                marker = victim / "marker.txt"
                marker.write_text("protected", encoding="utf-8")
                linked_directory = root / "system" / directory_name
                linked_directory.parent.mkdir()
                self.create_directory_link(linked_directory, victim)

                with self.assertRaises(clear_migrations.CleanupError):
                    clear_migrations.build_removal_plan(root)

                self.assertTrue(linked_directory.exists())
                self.assertTrue(victim.is_dir())
                self.assertTrue(marker.is_file())


class TemporaryCliTests(SimpleTestCase):

    def create_temp_project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        shutil.copy2(PROJECT_ROOT / "clear_migrations.py", root / "clear_migrations.py")
        (root / "manage.py").write_text("", encoding="utf-8")
        (root / "lvjiujitsu").mkdir()
        (root / "lvjiujitsu" / "settings.py").write_text("", encoding="utf-8")
        migrations = root / "system" / "migrations"
        migrations.mkdir(parents=True)
        (migrations / "__init__.py").write_text("", encoding="utf-8")
        (root / ".env").write_text(LOCAL_ENV_CONTENT, encoding="utf-8")
        return root

    def run_cli(self, root: Path) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        for key in CLEARED_ENVIRONMENT:
            environment.pop(key, None)
        environment["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "clear_migrations.py"],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_cli_refusal_preserves_link_and_victim(self) -> None:
        root = self.create_temp_project()
        victim = root / "protected"
        victim.mkdir()
        marker = victim / "marker.txt"
        marker.write_text("protected", encoding="utf-8")
        runtime_link = root / "staticfiles"
        try:
            runtime_link.symlink_to(victim, target_is_directory=True)
        except OSError:
            result = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(runtime_link), str(victim)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                self.skipTest("Link e junction indisponíveis neste Windows.")

        result = self.run_cli(root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("[ERRO]", result.stderr)
        self.assertIn("Link ou junction recusado", result.stderr)
        self.assertTrue(runtime_link.exists())
        self.assertTrue(victim.is_dir())
        self.assertTrue(marker.is_file())

    def test_cli_completes_documented_cycle_in_normal_temporary_tree(self) -> None:
        root = self.create_temp_project()
        (root / "db.sqlite3").write_text("database", encoding="utf-8")
        migrations = root / "system" / "migrations"
        (migrations / "0001_initial.py").write_text("migration", encoding="utf-8")
        cache = root / "system" / "__pycache__"
        cache.mkdir()
        (cache / "module.pyc").write_text("cache", encoding="utf-8")
        runtime = root / "media"
        runtime.mkdir()
        (runtime / "upload.txt").write_text("runtime", encoding="utf-8")

        result = self.run_cli(root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Limpeza concluída", result.stdout)
        self.assertFalse((root / "db.sqlite3").exists())
        self.assertFalse((migrations / "0001_initial.py").exists())
        self.assertFalse(cache.exists())
        self.assertFalse(runtime.exists())
        clear_migrations.verify_cleanup(root)


class DatabaseTargetGuardTests(SimpleTestCase):

    def make_temp_dir(self) -> Path:
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        return Path(directory)

    def test_targets_inside_root_are_accepted(self) -> None:
        clear_migrations.validate_database_targets(self.make_temp_dir())

    def test_target_escaping_root_is_refused(self) -> None:
        root = self.make_temp_dir()

        with mock.patch.object(
            clear_migrations, "DATABASE_FILE_NAMES", ("../db.sqlite3",)
        ):
            with self.assertRaises(RuntimeError) as raised:
                clear_migrations.validate_database_targets(root)

        self.assertIn("fora da raiz", str(raised.exception))
