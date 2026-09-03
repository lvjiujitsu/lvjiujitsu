import json
import hashlib
import importlib.util
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SKILL = pathlib.Path(__file__).resolve().parents[1]
STATE = SKILL / "scripts" / "state.py"
GIT_FLOW = SKILL / "scripts" / "git_flow.py"
QUALITY = SKILL / "scripts" / "quality_scan.py"
REPOSITORY = SKILL.parents[2]
CI = REPOSITORY / ".github" / "workflows" / "ci.yml"
SPEC = importlib.util.spec_from_file_location("lvjiujitsu_git_flow", GIT_FLOW)
GIT_FLOW_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GIT_FLOW_MODULE)
STATE_SPEC = importlib.util.spec_from_file_location("lvjiujitsu_state", STATE)
STATE_MODULE = importlib.util.module_from_spec(STATE_SPEC)
STATE_SPEC.loader.exec_module(STATE_MODULE)


def run(args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def remove_tree(path):
    if not path.exists():
        return
    for item in path.rglob("*"):
        if item.is_file():
            item.chmod(stat.S_IWRITE)
    shutil.rmtree(path)


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = pathlib.Path(tempfile.mkdtemp(prefix="lvjiujitsu-agent-test-"))
        self.repo = self.temporary / "repo"
        self.remote = self.temporary / "remote.git"
        self.repo.mkdir()
        run(["git", "init", "-b", "stage"], self.repo)
        run(["git", "config", "user.email", "agent@example.invalid"], self.repo)
        run(["git", "config", "user.name", "Agent Contract"], self.repo)
        (self.repo / "app.py").write_text("value = 1\n", encoding="utf-8")
        (self.repo / "page.html").write_text("<main>ok</main>\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "baseline"], self.repo)
        run(["git", "branch", "developer"], self.repo)
        run(["git", "init", "--bare", str(self.remote)], self.temporary)
        run(["git", "remote", "add", "origin", str(self.remote)], self.repo)
        run(["git", "push", "origin", "stage", "developer"], self.repo)

    def tearDown(self):
        remove_tree(self.temporary)

    def state(self, *args, check=True):
        return run([sys.executable, str(STATE), *args], self.repo, check=check)

    def flow(self, *args, check=True):
        return run([sys.executable, str(GIT_FLOW), *args], self.repo, check=check)

    def inspect_all(self, owner, path):
        chunks = []
        while True:
            payload = json.loads(
                self.state("inspect", "--owner", owner, "--path", path).stdout
            )
            chunks.append(payload)
            if payload["complete"]:
                return chunks

    def complete_ui_gate(self, owner, scope):
        self.state("ui-require", "--owner", owner, "--prd", scope)
        state_path = pathlib.Path(self.state("path").stdout.strip())
        evidence = state_path.parent / "evidence"
        evidence.mkdir(exist_ok=True)
        combinations = (
            ("desktop", "light", ("happy",)),
            ("desktop", "dark", ("invalid",)),
            ("mobile", "light", ("error",)),
            ("mobile", "dark", ("permission",)),
        )
        for index, (viewport, theme, states) in enumerate(combinations):
            screenshot = evidence / f"{scope.replace('/', '-')}-{index}.png"
            screenshot.write_bytes(b"\x89PNG\r\n\x1a\nproof")
            self.state(
                "ui-evidence",
                "--owner",
                owner,
                "--prd",
                scope,
                "--route",
                "/administration/test/",
                "--viewport",
                viewport,
                "--theme",
                theme,
                "--states",
                *states,
                "--screenshot",
                str(screenshot),
                "--console-errors",
                "0",
                "--terminal-errors",
                "0",
            )

    def test_state_requires_complete_coverage_and_resolved_prds(self):
        owner = "contract-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        self.assertNotEqual(self.state("complete-global", "--owner", owner, check=False).returncode, 0)
        self.assertNotEqual(
            self.state(
                "audit",
                "--owner",
                owner,
                "--path",
                "app.py",
                "--responsibility",
                "configuration",
                "--consumers",
                "page.html",
                "--risks",
                "configuration",
                check=False,
            ).returncode,
            0,
        )
        self.inspect_all(owner, "app.py")
        self.inspect_all(owner, "page.html")
        self.state("audit", "--owner", owner, "--path", "app.py", "--responsibility", "configuration", "--consumers", "page.html", "--risks", "configuration")
        self.state("audit", "--owner", owner, "--path", "page.html", "--responsibility", "template", "--consumers", "app.py", "--risks", "ui")
        self.state("complete-global", "--owner", owner)
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-001-fix.md", "--status", "found")
        self.assertNotEqual(self.state("assert-ready", "--owner", owner, check=False).returncode, 0)
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-001-fix.md", "--status", "blocked")
        self.assertNotEqual(self.state("assert-ready", "--owner", owner, check=False).returncode, 0)
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-001-fix.md", "--status", "resolved")
        self.complete_ui_gate(owner, "global")
        self.state("assert-ready", "--owner", owner)
        self.state("invalidate", "--owner", owner, "--path", "app.py")
        self.assertNotEqual(self.state("complete-global", "--owner", owner, check=False).returncode, 0)
        self.inspect_all(owner, "app.py")
        self.state("audit", "--owner", owner, "--path", "app.py", "--responsibility", "configuration", "--consumers", "page.html", "--risks", "configuration")
        self.state("complete-global", "--owner", owner)
        self.state("release", "--owner", owner)

    def test_open_prds_carry_over_and_a_false_positive_can_be_dismissed(self):
        owner = "backlog-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        for path, responsibility in (("app.py", "configuration"), ("page.html", "template")):
            self.inspect_all(owner, path)
            self.state(
                "audit", "--owner", owner, "--path", path,
                "--responsibility", responsibility, "--risks", "none",
            )
        self.state("complete-global", "--owner", owner)
        self.complete_ui_gate(owner, "global")
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-010-fix.md", "--status", "resolved")
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-011-next.md", "--status", "found")
        self.state("assert-ready", "--owner", owner)
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-012-stop.md", "--status", "blocked")
        self.assertNotEqual(self.state("assert-ready", "--owner", owner, check=False).returncode, 0)
        thin = self.state(
            "prd", "--owner", owner, "--path", "docs/prd/PRD-012-stop.md",
            "--status", "dismissed", "--reason", "curto", check=False,
        )
        self.assertNotEqual(thin.returncode, 0)
        self.state(
            "prd", "--owner", owner, "--path", "docs/prd/PRD-012-stop.md", "--status", "dismissed",
            "--reason", "Investigado em profundidade: o defeito descrito nao existe no codigo atual.",
        )
        self.state("assert-ready", "--owner", owner)
        payload = json.loads(self.state("summary").stdout)
        self.assertEqual(payload["prds_dismissed"], 1)
        self.assertEqual(payload["prds_found"], ["docs/prd/PRD-011-next.md"])

    def grant_receipt(self, worktree, failed=False):
        head = run(["git", "rev-parse", "HEAD"], worktree).stdout.strip()
        path = self.repo / ".git" / "lvjiujitsu-agent" / "gate-receipt.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"head": head, "gates": {"tests": 1 if failed else 0}}), encoding="utf-8"
        )
        return head

    def test_publish_refuses_without_a_green_gate_receipt(self):
        worktree = self.repo / ".agents-runtime" / "worktrees" / "receipt"
        branch = "feature/prd-007-receipt"
        developer = run(["git", "rev-parse", "origin/developer"], self.repo).stdout.strip()
        self.flow("prepare", "--path", str(worktree), "--branch", branch, "--execute")
        missing = self.flow(
            "publish", "--path", str(worktree), "--expected-developer", developer,
            "--execute", check=False,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("No gate receipt", missing.stderr)
        self.grant_receipt(worktree, failed=True)
        red = self.flow(
            "publish", "--path", str(worktree), "--expected-developer", developer,
            "--execute", check=False,
        )
        self.assertNotEqual(red.returncode, 0)
        self.assertIn("records a failure", red.stderr)
        (worktree / "later.py").write_text("later = True\n", encoding="utf-8")
        run(["git", "add", "later.py"], worktree)
        run(["git", "commit", "-m", "moves head"], worktree)
        stale = self.flow(
            "publish", "--path", str(worktree), "--expected-developer", developer,
            "--execute", check=False,
        )
        self.assertNotEqual(stale.returncode, 0)
        self.grant_receipt(worktree)
        self.flow("publish", "--path", str(worktree), "--expected-developer", developer, "--execute")

    def test_publish_refuses_stale_stage_then_refreshes_and_cleans(self):
        worktree = self.repo / ".agents-runtime" / "worktrees" / "cycle"
        branch = "feature/prd-001-contract"
        initial_developer = run(["git", "rev-parse", "origin/developer"], self.repo).stdout.strip()
        self.flow("prepare", "--path", str(worktree), "--branch", branch, "--execute")
        self.grant_receipt(worktree)
        self.flow("publish", "--path", str(worktree), "--expected-developer", initial_developer, "--execute")
        synchronized = run(["git", "rev-parse", "origin/developer"], self.repo).stdout.strip()
        (worktree / "fix.py").write_text("fixed = True\n", encoding="utf-8")
        run(["git", "add", "fix.py"], worktree)
        run(["git", "commit", "-m", "agent fix"], worktree)
        (self.repo / "human.py").write_text("human = True\n", encoding="utf-8")
        run(["git", "add", "human.py"], self.repo)
        run(["git", "commit", "-m", "human stage change"], self.repo)
        run(["git", "push", "origin", "stage"], self.repo)
        stage = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        refused = self.flow("publish", "--path", str(worktree), "--expected-developer", synchronized, "--execute", check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("current origin/stage", refused.stderr)
        self.flow("refresh", "--path", str(worktree), "--execute")
        head = self.grant_receipt(worktree)
        self.flow("publish", "--path", str(worktree), "--expected-developer", synchronized, "--execute")
        remote_stage = run(["git", "rev-parse", "origin/stage"], self.repo).stdout.strip()
        remote_developer = run(["git", "rev-parse", "origin/developer"], self.repo).stdout.strip()
        self.assertEqual(remote_stage, stage)
        self.assertEqual(remote_developer, head)
        self.assertEqual(run(["git", "merge-base", "--is-ancestor", stage, remote_developer], self.repo, check=False).returncode, 0)
        self.flow("cleanup", "--path", str(worktree), "--branch", branch, "--head", head, "--execute")
        self.assertFalse(worktree.exists())
        self.assertNotEqual(run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], self.repo, check=False).returncode, 0)

    def test_pull_request_returns_no_changes_without_calling_github(self):
        body = self.repo / "body.md"
        body.write_text("Ready\n", encoding="utf-8")
        result = self.flow(
            "pull-request",
            "--title",
            "No changes",
            "--body-file",
            str(body),
            "--head",
            run(["git", "rev-parse", "origin/developer"], self.repo).stdout.strip(),
            "--execute",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "no_changes")
        self.assertEqual(payload["ahead"], 0)

    def test_complete_cycle_clears_transient_state(self):
        owner = "complete-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        state_path = pathlib.Path(self.state("path").stdout.strip())
        worktree = self.repo / ".agents-runtime" / "worktrees" / "finished"
        worktree.mkdir(parents=True)
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        for path in ("app.py", "page.html"):
            self.inspect_all(owner, path)
            self.state(
                "audit",
                "--owner",
                owner,
                "--path",
                path,
                "--responsibility",
                "configuration" if path.endswith(".py") else "template",
                "--risks",
                "configuration" if path.endswith(".py") else "ui",
            )
        self.state("complete-global", "--owner", owner)
        self.complete_ui_gate(owner, "global")
        self.state(
            "phase",
            "--owner",
            owner,
            "--name",
            "cleanup",
            "--feature",
            "feature/prd-002-finished",
            "--worktree",
            str(worktree),
        )
        refused = self.state(
            "complete-cycle",
            "--owner",
            owner,
            "--stage-sha",
            baseline,
            check=False,
        )
        self.assertNotEqual(refused.returncode, 0)
        worktree.rmdir()
        self.state(
            "complete-cycle", "--owner", owner, "--stage-sha", baseline
        )
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["phase"], "idle")
        self.assertIsNone(data["feature"])
        self.assertIsNone(data["worktree"])
        self.assertEqual(data["last_stage_sha"], baseline)
        self.state("release", "--owner", owner)

    def test_inspection_emits_all_chunks_and_invalidates_legacy_coverage(self):
        text = "linha completa\n" * 5000
        binary = b"\x00\xff\x01\xfe"
        (self.repo / "large.txt").write_text(text, encoding="utf-8")
        (self.repo / "binary.bin").write_bytes(binary)
        run(["git", "add", "large.txt", "binary.bin"], self.repo)
        run(["git", "commit", "-m", "inspection fixtures"], self.repo)
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        owner = "inspection-test"
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        chunks = self.inspect_all(owner, "large.txt")
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(item["content"] for item in chunks), text)
        self.assertEqual(chunks[-1]["content_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(chunks[-1]["line_count"], 5000)
        binary_result = self.inspect_all(owner, "binary.bin")[-1]
        self.assertTrue(binary_result["binary"])
        self.assertTrue(binary_result["complete"])
        state_path = pathlib.Path(self.state("path").stdout.strip())
        legacy = json.loads(state_path.read_text(encoding="utf-8"))
        legacy["schema_version"] = 1
        legacy["global_status"] = "global_complete"
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        self.state("init", "--owner", owner, "--baseline", baseline)
        migrated = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["global_status"], "global_pending")
        self.assertTrue(all(item["status"] == "pending" for item in migrated["files"].values()))
        self.state("release", "--owner", owner)

    def test_ui_gate_requires_real_matrix_before_resolution(self):
        owner = "ui-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        prd = "docs/prd/PRD-001-ui.md"
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        for path in ("app.py", "page.html"):
            self.inspect_all(owner, path)
            self.state(
                "audit",
                "--owner",
                owner,
                "--path",
                path,
                "--responsibility",
                "configuration" if path.endswith(".py") else "template",
                "--risks",
                "configuration" if path.endswith(".py") else "ui",
            )
        self.state("complete-global", "--owner", owner)
        self.state("prd", "--owner", owner, "--path", prd, "--status", "found")
        self.state("ui-require", "--owner", owner, "--prd", prd)
        refused = self.state(
            "prd", "--owner", owner, "--path", prd, "--status", "resolved", check=False
        )
        self.assertNotEqual(refused.returncode, 0)
        self.complete_ui_gate(owner, prd)
        self.state("prd", "--owner", owner, "--path", prd, "--status", "resolved")
        self.state("assert-ready", "--owner", owner)
        self.state("release", "--owner", owner)

    def test_ci_contract_runs_all_required_gates(self):
        content = CI.read_text(encoding="utf-8")
        for required in (
            "compileall",
            "manage.py check",
            "showmigrations --plan",
            "makemigrations --check --dry-run",
            "collectstatic --noinput --dry-run",
            "manage.py test",
            "test_contract.py",
            "quality_scan.py --all",
        ):
            self.assertIn(required, content)

    def test_repository_contract_exposes_only_current_agents(self):
        contract = (REPOSITORY / "AGENTS.md").read_text(encoding="utf-8")
        codex_agents = list((REPOSITORY / ".codex" / "agents").glob("*.toml"))
        claude_agents = list((REPOSITORY / ".claude" / "agents").glob("*.md"))
        skills = [
            item.name
            for item in (REPOSITORY / ".agents" / "skills").iterdir()
            if item.is_dir() and item.name.startswith("lvjiujitsu-")
        ]
        claude_skills = [
            item.name
            for item in (REPOSITORY / ".claude" / "skills").iterdir()
            if item.is_dir() and item.name.startswith("lvjiujitsu-")
        ]
        self.assertEqual(
            sorted(item.name for item in codex_agents), ["lvjiujitsu-agent-developer.toml"]
        )
        self.assertEqual(
            sorted(item.name for item in claude_agents),
            [
                "lvjiujitsu-agent-clean-code.md",
                "lvjiujitsu-agent-developer.md",
                "lvjiujitsu-agent-visual.md",
            ],
        )
        canonical_skills = [
            "lvjiujitsu-autonomous-developer",
            "lvjiujitsu-clean-code",
            "lvjiujitsu-visual-auditor",
        ]
        expected_claude_skills = sorted(canonical_skills + ["lvjiujitsu-remote-refresh"])
        self.assertEqual(sorted(skills), canonical_skills)
        self.assertEqual(sorted(claude_skills), expected_claude_skills)
        for name in canonical_skills:
            adapter = REPOSITORY / ".claude" / "skills" / name / "SKILL.md"
            self.assertIn(f".agents/skills/{name}/SKILL.md", adapter.read_text(encoding="utf-8"))
            self.assertFalse((REPOSITORY / ".claude" / "skills" / name / "scripts").exists())
        self.assertFalse((REPOSITORY / ".cursor").exists())
        self.assertIn("Quatro agentes autônomos", contract)
        for removed in ("prd-review", "final-review", "agent_queue", "autonomous-pipeline"):
            self.assertNotIn(removed, contract)

    def dom_report(self, name, viewport, theme, assertions=3, **overrides):
        root = pathlib.Path(self.state("path").stdout.strip()).parent / "evidence"
        root.mkdir(parents=True, exist_ok=True)
        payload = {
            "screenshot_error": "the Browser pane is not displayed",
            "url": "http://localhost:8000/reservation/",
            "theme": theme,
            "viewport_width": 1440 if viewport == "desktop" else 390,
            "assertions": [
                {
                    "selector": f".field-error-{index}",
                    "property": "color",
                    "observed": "rgb(190, 30, 45)",
                    "expected": "var(--color-danger)",
                }
                for index in range(assertions)
            ],
        }
        payload.update(overrides)
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def record_dom_evidence(self, owner, scope, viewport, theme, report):
        return self.state(
            "ui-evidence",
            "--owner",
            owner,
            "--prd",
            scope,
            "--route",
            "/reservation/",
            "--viewport",
            viewport,
            "--theme",
            theme,
            "--states",
            *STATE_MODULE.UI_STATES,
            "--dom-report",
            report,
            "--console-errors",
            "0",
            "--terminal-errors",
            "0",
            check=False,
        )

    def test_dom_report_replaces_screenshot_only_with_concrete_assertions(self):
        owner = "dom-test"
        scope = "global"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        self.state("ui-require", "--owner", owner, "--prd", scope)
        thin = self.dom_report("thin.json", "desktop", "light", assertions=2)
        self.assertNotEqual(
            self.record_dom_evidence(owner, scope, "desktop", "light", thin).returncode, 0
        )
        without_failure = self.dom_report(
            "no-failure.json", "desktop", "light", screenshot_error="  "
        )
        self.assertNotEqual(
            self.record_dom_evidence(owner, scope, "desktop", "light", without_failure).returncode,
            0,
        )
        narrow = self.dom_report("narrow.json", "desktop", "light", viewport_width=390)
        self.assertNotEqual(
            self.record_dom_evidence(owner, scope, "desktop", "light", narrow).returncode, 0
        )
        for viewport in ("desktop", "mobile"):
            for theme in ("light", "dark"):
                report = self.dom_report(f"{viewport}-{theme}.json", viewport, theme)
                self.assertEqual(
                    self.record_dom_evidence(owner, scope, viewport, theme, report).returncode, 0
                )
        summary = json.loads(self.state("summary").stdout)
        self.assertEqual(summary["ui_gates_incomplete"], [])
        self.assertEqual(summary["ui_visual_confirmation_pending"], [scope])

    def test_new_round_reaudits_every_file_after_global_complete(self):
        owner = "round-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        for path, responsibility in (("app.py", "configuration"), ("page.html", "template")):
            self.inspect_all(owner, path)
            self.state(
                "audit",
                "--owner",
                owner,
                "--path",
                path,
                "--responsibility",
                responsibility,
                "--risks",
                "none",
            )
        self.state("complete-global", "--owner", owner)
        completed = json.loads(self.state("summary").stdout)
        self.assertEqual(completed["global_status"], "global_complete")
        self.assertEqual(completed["files_audited"], 2)
        self.state("init", "--owner", owner, "--baseline", baseline)
        restarted = json.loads(self.state("summary").stdout)
        self.assertEqual(restarted["global_status"], "global_pending")
        self.assertEqual(restarted["files_audited"], 0)
        self.assertEqual(restarted["files_pending"], 2)
        self.assertEqual(restarted["next_pending"], ["app.py", "page.html"])
        self.assertNotEqual(self.state("complete-global", "--owner", owner, check=False).returncode, 0)

    def test_pending_batch_blocks_the_next_round_restart(self):
        owner = "batch-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        for path, responsibility in (("app.py", "configuration"), ("page.html", "template")):
            self.inspect_all(owner, path)
            self.state(
                "audit",
                "--owner",
                owner,
                "--path",
                path,
                "--responsibility",
                responsibility,
                "--risks",
                "none",
            )
        self.state("complete-global", "--owner", owner)
        self.state("prd", "--owner", owner, "--path", "docs/prd/PRD-001-fix.md", "--status", "blocked")
        self.state("init", "--owner", owner, "--baseline", baseline)
        held = json.loads(self.state("summary").stdout)
        self.assertEqual(held["global_status"], "global_complete")
        self.assertEqual(held["files_audited"], 2)
        self.state(
            "phase", "--owner", owner, "--name", "implementing", "--feature", "feature/prd-003-x"
        )
        self.state("init", "--owner", owner, "--baseline", baseline)
        still_held = json.loads(self.state("summary").stdout)
        self.assertEqual(still_held["files_audited"], 2)
        self.state(
            "prd", "--owner", owner, "--path", "docs/prd/PRD-001-fix.md", "--status", "resolved"
        )
        self.state("phase", "--owner", owner, "--name", "idle", "--feature", "", "--worktree", "")
        self.state("init", "--owner", owner, "--baseline", baseline)
        released = json.loads(self.state("summary").stdout)
        self.assertEqual(released["global_status"], "global_pending")
        self.assertEqual(released["files_audited"], 0)

    def test_ui_gates_reset_on_restart_with_the_same_baseline(self):
        owner = "ui-restart-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        started = json.loads(self.state("summary").stdout)
        self.assertTrue(started["ui_required"])
        for path, responsibility in (("app.py", "configuration"), ("page.html", "template")):
            self.inspect_all(owner, path)
            self.state(
                "audit",
                "--owner",
                owner,
                "--path",
                path,
                "--responsibility",
                responsibility,
                "--risks",
                "ui" if path.endswith(".html") else "none",
            )
        self.complete_ui_gate(owner, "global")
        self.state("complete-global", "--owner", owner)
        settled = json.loads(self.state("summary").stdout)
        self.assertEqual(settled["global_status"], "global_complete")
        self.assertEqual(settled["ui_gates_incomplete"], [])
        state_path = pathlib.Path(self.state("path").stdout.strip())
        settled_raw = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIn("global", settled_raw["ui_gates"])
        self.assertTrue(STATE_MODULE.ui_gate_complete(settled_raw["ui_gates"]["global"]))

        self.state("init", "--owner", owner, "--baseline", baseline)
        restarted = json.loads(self.state("summary").stdout)
        self.assertEqual(restarted["global_status"], "global_pending")
        self.assertEqual(restarted["files_audited"], 0)
        self.assertTrue(restarted["ui_required"])
        restarted_raw = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            restarted_raw["ui_gates"],
            {},
            "a rodada nova reaudita tudo do zero, mas herdou evidência de UI satisfeita da rodada anterior",
        )

    def test_unfinished_round_keeps_progress_when_stage_advances(self):
        owner = "resume-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        self.inspect_all(owner, "app.py")
        self.state(
            "audit",
            "--owner",
            owner,
            "--path",
            "app.py",
            "--responsibility",
            "configuration",
            "--risks",
            "none",
        )
        (self.repo / "page.html").write_text("<main>changed</main>\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "avanco"], self.repo)
        advanced = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("init", "--owner", owner, "--baseline", advanced)
        resumed = json.loads(self.state("summary").stdout)
        self.assertEqual(resumed["files_audited"], 1)
        self.assertEqual(resumed["next_pending"], ["page.html"])

    def test_summary_reports_progress_and_next_pending(self):
        owner = "summary-test"
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        payload = json.loads(self.state("summary").stdout)
        self.assertEqual(payload["files_total"], 2)
        self.assertEqual(payload["files_audited"], 0)
        self.assertEqual(payload["next_pending"], ["app.py", "page.html"])
        self.assertEqual(payload["lease_owner"], owner)
        self.assertNotIn("files", payload)
        self.inspect_all(owner, "app.py")
        self.state(
            "audit",
            "--owner",
            owner,
            "--path",
            "app.py",
            "--responsibility",
            "configuration",
            "--risks",
            "none",
        )
        updated = json.loads(self.state("summary").stdout)
        self.assertEqual(updated["files_audited"], 1)
        self.assertEqual(updated["next_pending"], ["page.html"])

    def test_inspect_emits_non_ascii_under_legacy_console_encoding(self):
        owner = "encoding-test"
        (self.repo / "acentos.py").write_text("acentuação\n" * 4000, encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "acentos"], self.repo)
        baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.state("acquire", "--owner", owner)
        self.state("init", "--owner", owner, "--baseline", baseline)
        legacy = subprocess.run(
            [sys.executable, str(STATE), "inspect", "--owner", owner, "--path", "acentos.py"],
            cwd=self.repo,
            check=False,
            capture_output=True,
            env=dict(os.environ, PYTHONIOENCODING="cp1252"),
        )
        self.assertEqual(legacy.returncode, 0, legacy.stderr.decode("utf-8", "replace"))
        payload = json.loads(legacy.stdout.decode("utf-8"))
        self.assertFalse(payload["complete"])
        self.assertGreater(payload["offset"], 0)
        self.assertLessEqual(payload["offset"], STATE_MODULE.INSPECTION_CHUNK_BYTES)
        self.assertEqual(len(payload["content"].encode("utf-8")), payload["offset"])
        self.assertIn("acentuação", payload["content"])
        chunks = self.inspect_all(owner, "acentos.py")
        self.assertTrue(chunks[-1]["complete"])
        self.assertEqual(chunks[-1]["offset"], chunks[-1]["byte_count"])

    def test_remote_check_requires_exact_head_and_success(self):
        head = "a" * 40
        pending = {"headRefOid": head, "statusCheckRollup": []}
        self.assertEqual(
            GIT_FLOW_MODULE.required_check_state(
                pending, head, "quality-gates"
            ),
            "pending",
        )
        with self.assertRaises(RuntimeError):
            GIT_FLOW_MODULE.required_check_state(
                {"headRefOid": "b" * 40, "statusCheckRollup": []},
                head,
                "quality-gates",
            )
        with self.assertRaises(RuntimeError):
            GIT_FLOW_MODULE.required_check_state(
                {
                    "headRefOid": head,
                    "statusCheckRollup": [
                        {
                            "name": "quality-gates",
                            "status": "COMPLETED",
                            "conclusion": "FAILURE",
                        }
                    ],
                },
                head,
                "quality-gates",
            )
        success = {
            "headRefOid": head,
            "statusCheckRollup": [
                {
                    "name": "quality-gates",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                }
            ],
        }
        self.assertEqual(
            GIT_FLOW_MODULE.required_check_state(
                success, head, "quality-gates"
            ),
            "success",
        )

    def test_commit_stages_only_validated_feature_worktree(self):
        worktree = self.repo / ".agents-runtime" / "worktrees" / "commit-cycle"
        branch = "feature/prd-004-commit-contract"
        self.flow(
            "prepare",
            "--path",
            str(worktree),
            "--branch",
            branch,
            "--execute",
        )
        before = run(["git", "rev-parse", "HEAD"], worktree).stdout.strip()
        (worktree / "fix.py").write_text("fixed = True\n", encoding="utf-8")

        preview = self.flow(
            "commit",
            "--path",
            str(worktree),
            "--branch",
            branch,
            "--message",
            "contract commit",
        )
        self.assertEqual(json.loads(preview.stdout)["state"], "required")
        self.assertEqual(run(["git", "rev-parse", "HEAD"], worktree).stdout.strip(), before)

        result = self.flow(
            "commit",
            "--path",
            str(worktree),
            "--branch",
            branch,
            "--message",
            "contract commit",
            "--execute",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "committed")
        self.assertNotEqual(payload["head"], before)
        self.assertEqual(run(["git", "status", "--porcelain"], worktree).stdout, "")

    def test_commit_refuses_operator_checkout_and_wrong_branch(self):
        refused_path = self.flow(
            "commit",
            "--path",
            str(self.repo),
            "--branch",
            "feature/prd-001-contract",
            "--message",
            "invalid",
            "--execute",
            check=False,
        )
        self.assertNotEqual(refused_path.returncode, 0)

        worktree = self.repo / ".agents-runtime" / "worktrees" / "wrong-branch"
        self.flow(
            "prepare",
            "--path",
            str(worktree),
            "--branch",
            "feature/prd-005-correct",
            "--execute",
        )
        refused_branch = self.flow(
            "commit",
            "--path",
            str(worktree),
            "--branch",
            "feature/prd-006-other",
            "--message",
            "invalid",
            "--execute",
            check=False,
        )
        self.assertNotEqual(refused_branch.returncode, 0)

    def test_quality_scan_detects_supported_comments_and_docstrings(self):
        clean = run([sys.executable, str(QUALITY), "--all"], self.repo, check=False)
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        (self.repo / "app.py").write_text('"""documentation"""\nvalue = 1  # note\n', encoding="utf-8")
        (self.repo / "page.html").write_text("<main>ok</main><!-- note -->\n", encoding="utf-8")
        (self.repo / "app.js").write_text('const url = "https://example.invalid"; const value = 1; // note\n', encoding="utf-8")
        run(["git", "add", "app.js"], self.repo)
        scan = run([sys.executable, str(QUALITY), "--all"], self.repo, check=False)
        self.assertEqual(scan.returncode, 1)
        findings = json.loads(scan.stdout)["findings"]
        kinds = {(item["path"], item["kind"]) for item in findings}
        self.assertIn(("app.py", "docstring"), kinds)
        self.assertIn(("app.py", "comment"), kinds)
        self.assertIn(("page.html", "comment"), kinds)
        self.assertIn(("app.js", "comment"), kinds)

    def test_quality_scan_detects_the_django_comment_tag(self):
        (self.repo / "note.html").write_text(
            "{% comment %}\nRacional de design.\n{% endcomment %}\n<main>ok</main>\n",
            encoding="utf-8",
        )
        run(["git", "add", "note.html"], self.repo)

        scan = run([sys.executable, str(QUALITY), "--all"], self.repo, check=False)

        self.assertEqual(scan.returncode, 1)
        findings = json.loads(scan.stdout)["findings"]
        kinds = {(item["path"], item["kind"]) for item in findings}
        self.assertIn(("note.html", "comment"), kinds)

    def test_quality_scan_all_does_not_require_remote_developer(self):
        run(["git", "update-ref", "-d", "refs/remotes/origin/developer"], self.repo)
        scan = run([sys.executable, str(QUALITY), "--all"], self.repo, check=False)
        self.assertEqual(scan.returncode, 0, scan.stdout + scan.stderr)


if __name__ == "__main__":
    unittest.main()
