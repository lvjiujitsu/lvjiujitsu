import json
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest


SKILL = pathlib.Path(__file__).resolve().parents[1]
VISUAL_STATE = SKILL / "scripts" / "visual_state.py"


def run(args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def remove_tree(path):
    if not path.exists():
        return
    for item in path.rglob("*"):
        if item.is_file():
            item.chmod(stat.S_IWRITE)
    shutil.rmtree(path)


class VisualContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = pathlib.Path(tempfile.mkdtemp(prefix="lvjiujitsu-visual-test-"))
        self.repo = self.temporary / "repo"
        self.repo.mkdir()
        run(["git", "init", "-b", "stage"], self.repo)
        run(["git", "config", "user.email", "agent@example.invalid"], self.repo)
        run(["git", "config", "user.name", "Visual Contract"], self.repo)
        (self.repo / "page.html").write_text("<main>ok</main>\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "baseline"], self.repo)
        self.baseline = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.agent = self.repo / ".git" / "lvjiujitsu-agent"
        self.agent.mkdir(parents=True)
        (self.agent / "state.json").write_text(
            json.dumps({"lease": {"owner": "codex", "expires_at": time.time() + 3600,
                                  "heartbeat": time.time()}}),
            encoding="utf-8",
        )
        self.evidence = self.agent / "evidence"
        self.evidence.mkdir()
        self.visual("acquire", "--owner", "visual")
        self.routes = self.temporary / "routes.json"
        self.routes.write_text(
            json.dumps([{"name": "map", "url": "http://localhost:8010/map/", "access": "public"}]),
            encoding="utf-8",
        )

    def tearDown(self):
        remove_tree(self.temporary)

    def visual(self, *args, check=True):
        return run([sys.executable, str(VISUAL_STATE), *args], self.repo, check=check)

    def report(self, name, viewport, theme, **overrides):
        payload = {
            "url": "http://localhost:8010/map/",
            "theme": theme,
            "viewport_width": 1440 if viewport == "desktop" else 390,
            "viewport_height": 900 if viewport == "desktop" else 844,
            "document_scroll_width": 1440 if viewport == "desktop" else 390,
            "document_client_width": 1440 if viewport == "desktop" else 390,
            "console_errors": 0,
            "interactive_total": 12,
            "interactive_exercised": 12,
            "small_tap_targets": [],
            "contrast_failures": [],
            "overlaps": [],
            "findings": [],
        }
        payload.update(overrides)
        path = self.evidence / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def probe(self, viewport, theme, report, check=False):
        return self.visual(
            "probe", "--owner", "visual", "--route", "map",
            "--viewport", viewport, "--theme", theme, "--report", report, check=check,
        )

    def test_lease_is_private_to_this_lane_and_blocks_other_owners(self):
        self.visual("release", "--owner", "visual")
        self.visual("acquire", "--owner", "outro")
        self.assertNotEqual(
            self.visual("init", "--owner", "visual", "--baseline", self.baseline,
                        "--routes", str(self.routes), check=False).returncode,
            0,
        )
        code_lane = json.loads((self.agent / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(code_lane["lease"]["owner"], "codex")

    def test_a_dead_holder_loses_the_lease_after_the_heartbeat_goes_stale(self):
        self.visual("release", "--owner", "visual")
        self.visual("acquire", "--owner", "travado")
        state = pathlib.Path(self.visual("path").stdout.strip())
        payload = json.loads(state.read_text(encoding="utf-8"))
        payload["lease"]["heartbeat"] = time.time() - 3600
        state.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(self.visual("acquire", "--owner", "visual", check=False).returncode, 0)

    def test_probe_requires_every_interactive_element_exercised(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        partial = self.report("partial.json", "desktop", "light", interactive_exercised=9)
        self.assertNotEqual(self.probe("desktop", "light", partial).returncode, 0)

    def test_probe_rejects_mismatched_viewport_and_theme(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        narrow = self.report("narrow.json", "desktop", "light", viewport_width=390)
        self.assertNotEqual(self.probe("desktop", "light", narrow).returncode, 0)
        wrong_theme = self.report("theme.json", "desktop", "dark")
        self.assertNotEqual(self.probe("desktop", "light", wrong_theme).returncode, 0)

    def test_measured_defect_without_finding_is_refused(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        overflow = self.report("overflow.json", "mobile", "light", document_scroll_width=520)
        self.assertNotEqual(self.probe("mobile", "light", overflow).returncode, 0)
        console = self.report("console.json", "mobile", "light", console_errors=2)
        self.assertNotEqual(self.probe("mobile", "light", console).returncode, 0)
        tap = self.report(
            "tap.json", "mobile", "light",
            small_tap_targets=[{"selector": "button.x", "width": 20, "height": 20}],
        )
        self.assertNotEqual(self.probe("mobile", "light", tap).returncode, 0)
        declared = self.report(
            "declared.json", "mobile", "light", document_scroll_width=520,
            findings=[{"selector": "main", "problema": "overflow", "esperado": "sem rolagem lateral"}],
        )
        self.assertEqual(self.probe("mobile", "light", declared).returncode, 0)

    def test_probe_rejects_a_report_whose_url_does_not_match_the_route(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        wrong_url = self.report(
            "wrong-url.json", "desktop", "light", url="http://localhost:8010/other-route/"
        )
        self.assertNotEqual(self.probe("desktop", "light", wrong_url).returncode, 0)

    def test_complete_visual_refuses_measured_finding_without_a_registered_prd(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        for viewport in ("desktop", "mobile"):
            for theme in ("light", "dark"):
                overrides = {}
                if viewport == "mobile" and theme == "light":
                    overrides = {
                        "document_scroll_width": 520,
                        "findings": [
                            {"selector": "main", "problema": "overflow", "esperado": "sem rolagem lateral"}
                        ],
                    }
                report = self.report(f"{viewport}-{theme}.json", viewport, theme, **overrides)
                self.assertEqual(self.probe(viewport, theme, report).returncode, 0)
        self.assertNotEqual(
            self.visual("complete-visual", "--owner", "visual", check=False).returncode,
            0,
            "achado medido sem PRD registrada não pode fechar a cobertura visual",
        )
        self.visual("finding", "--owner", "visual", "--path", "docs/prd/PRD-999-x.md", "--status", "found")
        self.visual("complete-visual", "--owner", "visual")

    def test_coverage_requires_the_four_combinations(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        self.assertNotEqual(self.visual("complete-visual", "--owner", "visual", check=False).returncode, 0)
        for viewport in ("desktop", "mobile"):
            for theme in ("light", "dark"):
                report = self.report(f"{viewport}-{theme}.json", viewport, theme)
                self.assertEqual(self.probe(viewport, theme, report).returncode, 0)
        payload = json.loads(self.visual("summary").stdout)
        self.assertEqual(payload["routes_pending"], 0)
        self.visual("complete-visual", "--owner", "visual")
        self.visual("finding", "--owner", "visual", "--path", "docs/prd/PRD-040-x.md", "--status", "found")
        self.assertNotEqual(self.visual("assert-ready", "--owner", "visual", check=False).returncode, 0)
        self.visual("finding", "--owner", "visual", "--path", "docs/prd/PRD-040-x.md", "--status", "resolved")
        self.visual("assert-ready", "--owner", "visual")

    def test_new_round_resondes_every_route(self):
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        for viewport in ("desktop", "mobile"):
            for theme in ("light", "dark"):
                self.probe(viewport, theme, self.report(f"{viewport}-{theme}.json", viewport, theme))
        self.visual("complete-visual", "--owner", "visual")
        self.visual("complete-cycle", "--owner", "visual")
        self.visual("init", "--owner", "visual", "--baseline", self.baseline, "--routes", str(self.routes))
        payload = json.loads(self.visual("summary").stdout)
        self.assertEqual(payload["status"], "visual_pending")
        self.assertEqual(payload["routes_complete"], 0)
        self.assertEqual(payload["routes_pending"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
