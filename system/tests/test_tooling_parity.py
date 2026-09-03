import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ToolingParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cleanup = load_module(ROOT / 'clear_migrations.py', 'parity_cleanup')

    def test_other_project_process_on_shared_port_is_not_stopped(self):
        process = {'ProcessId': 991991, 'ParentProcessId': 0,
                   'ExecutablePath': 'C:/Python312/python.exe',
                   'CommandLine': 'python C:/other-project/manage.py runserver localhost:8000'}
        with mock.patch.object(self.cleanup, 'list_python_processes', return_value=[process]), \
             mock.patch.object(self.cleanup, 'listening_pids_on_project_ports', return_value={991991}, create=True), \
             mock.patch.object(self.cleanup, 'wait_processes_exit'), \
             mock.patch.object(self.cleanup.subprocess, 'run') as run, \
             mock.patch('sys.stdout', new_callable=io.StringIO):
            self.cleanup.stop_python_processes(ROOT)
        run.assert_not_called()

    def test_remote_file_cannot_be_disguised_by_local_process_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.env').write_text('DJANGO_ENVIRONMENT=hg\nDATABASE_URL=\n', encoding='utf-8')
            values = {key: 'fixture' for key in self.cleanup.REQUIRED_LOCAL_SEED_SETTINGS}
            with mock.patch.dict(os.environ, {**values, 'DJANGO_ENVIRONMENT': 'local'}, clear=True):
                with self.assertRaises(self.cleanup.CleanupError):
                    self.cleanup.validate_local_environment(root)

    def test_explicit_local_filename_uses_shared_fallback(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as shared:
            env = Path(shared) / '.env'
            env.write_text('DJANGO_ENVIRONMENT=local\nDATABASE_URL=\n', encoding='utf-8')
            values = {key: 'fixture' for key in self.cleanup.REQUIRED_LOCAL_SEED_SETTINGS}
            with mock.patch.dict(os.environ, {**values, 'DJANGO_ENV_FILE': '.env',
                    self.cleanup.SHARED_ENV_DIR_VARIABLE: shared}, clear=True):
                self.assertEqual(self.cleanup.validate_local_environment(Path(directory)), env.resolve())

    def test_check_mode_never_stops_or_removes(self):
        with mock.patch.object(self.cleanup, 'validate_project'), \
             mock.patch.object(self.cleanup, 'validate_local_environment', return_value=ROOT / '.env'), \
             mock.patch.object(self.cleanup, 'validate_database_targets'), \
             mock.patch.object(self.cleanup, 'build_removal_plan'), \
             mock.patch.object(self.cleanup, 'stop_python_processes') as stop, \
             mock.patch.object(self.cleanup, 'remove_database_files', return_value=(0, 0)) as remove, \
             mock.patch.object(self.cleanup, 'remove_pycache_directories'), \
             mock.patch.object(self.cleanup, 'remove_migration_files'), \
             mock.patch.object(self.cleanup, 'remove_runtime_artifacts'), \
             mock.patch.object(self.cleanup, 'verify_cleanup'), \
             mock.patch.object(sys, 'argv', ['clear_migrations.py', '--check']), \
             mock.patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(self.cleanup.main(['--check']), 0)
        stop.assert_not_called()
        remove.assert_not_called()

    def test_claude_adapters_resolve_canonical_skill(self):
        for skill in (ROOT / '.claude/skills').glob('*/SKILL.md'):
            if skill.parent.name.endswith('remote-refresh'):
                continue
            links = re.findall(r'\]\(([^)]+SKILL\.md)\)', skill.read_text(encoding='utf-8'))
            self.assertTrue(links, str(skill))
            for link in links:
                self.assertTrue((skill.parent / link).resolve().is_file(), f'{skill}: {link}')

    def test_settings_loader_finds_explicit_shared_file(self):
        path = ROOT / 'lvjiujitsu' / 'settings.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        body = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'config' for t in node.targets):
                break
            body.append(node)
        scope = {'__file__': str(path)}
        exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), scope)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as shared:
            scope['BASE_DIR'] = Path(directory)
            (Path(shared) / '.env').write_text('PARITY_FIXTURE=loaded\n', encoding='utf-8')
            with mock.patch.dict(os.environ, {'LVJIUJITSU_SHARED_ENV_DIR': shared, 'DJANGO_ENV_FILE': '.env'}, clear=True):
                self.assertEqual(scope['load_config']()('PARITY_FIXTURE'), 'loaded')

    def test_hook_reports_failure_without_modifying_files(self):
        hook = load_module(ROOT / '.claude/hooks/verify.py', 'parity_hook')
        result = mock.Mock(returncode=1, stderr='fixture failure', stdout='')
        with mock.patch.object(sys, 'stdin', io.StringIO('{}')), \
             mock.patch.object(sys, 'stderr', new_callable=io.StringIO) as stderr, \
             mock.patch.object(hook.subprocess, 'run', return_value=result) as run:
            self.assertEqual(hook.main(), 2)
        self.assertIn('fixture failure', stderr.getvalue())
        self.assertTrue(run.called)
        self.assertFalse(any('--apply' in call.args[0] for call in run.call_args_list))

    def test_hook_stops_recursion(self):
        hook = load_module(ROOT / '.claude/hooks/verify.py', 'parity_hook')
        with mock.patch.object(sys, 'stdin', io.StringIO(json.dumps({'stop_hook_active': True}))), \
             mock.patch.object(hook.subprocess, 'run') as run:
            self.assertEqual(hook.main(), 0)
        run.assert_not_called()

    def test_quality_scan_includes_untracked_source(self):
        scanner = ROOT / '.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py'
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git', 'init', '--quiet', directory], check=True, capture_output=True)
            (Path(directory) / 'new_module.py').write_text('value = 1 # fixture\n', encoding='utf-8')
            result = subprocess.run([sys.executable, str(scanner), '--all'], cwd=directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        findings = json.loads(result.stdout)['findings']
        self.assertTrue(any(item['path'] == 'new_module.py' and item['kind'] == 'comment' for item in findings))
