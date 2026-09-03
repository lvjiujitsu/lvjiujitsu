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
CLEAN_STATE = SKILL / "scripts" / "clean_state.py"
SPEC = __import__("importlib.util", fromlist=["util"]).spec_from_file_location(
    "lvjiujitsu_clean", CLEAN_STATE
)
CLEAN = __import__("importlib.util", fromlist=["util"]).module_from_spec(SPEC)
SPEC.loader.exec_module(CLEAN)


def run(args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def remove_tree(path):
    if not path.exists():
        return
    for item in path.rglob("*"):
        if item.is_file():
            item.chmod(stat.S_IWRITE)
    shutil.rmtree(path)


class CleanContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = pathlib.Path(tempfile.mkdtemp(prefix="lvjiujitsu-clean-test-"))
        self.repo = self.temporary / "repo"
        self.repo.mkdir()
        run(["git", "init", "-b", "stage"], self.repo)
        run(["git", "config", "user.email", "agent@example.invalid"], self.repo)
        run(["git", "config", "user.name", "Clean Contract"], self.repo)
        (self.repo / "clean.py").write_text("value = 1\n", encoding="utf-8")
        (self.repo / "dirty.py").write_text(
            "endereco = 'https://cdn.example.com/app.js'\n", encoding="utf-8"
        )
        (self.repo / "page.html").write_text("<main>Salvar</main>\n", encoding="utf-8")
        tests = self.repo / "system" / "tests"
        tests.mkdir(parents=True)
        (tests / "test_fixture.py").write_text(
            "email = 'agent@example.invalid'\n", encoding="utf-8"
        )
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
        self.clean("acquire", "--owner", "clean")

    def tearDown(self):
        remove_tree(self.temporary)

    def clean(self, *args, check=True):
        return run([sys.executable, str(CLEAN_STATE), *args], self.repo, check=check)

    def scan(self, path):
        return json.loads(self.clean("scan", "--path", path).stdout)

    def test_english_words_holding_portuguese_substrings_are_not_flagged(self):
        for name in ("reservation", "error_message_handler", "reserved_at", "errors"):
            self.assertEqual(CLEAN.suspect_identifier(name), "", name)
        for name in ("nome_cliente", "situacao", "endereco"):
            self.assertEqual(CLEAN.suspect_identifier(name), "identifier_portuguese", name)
        self.assertEqual(CLEAN.suspect_identifier("endereço"), "identifier_accented")

    def test_scan_reports_hardcode_outside_tests_and_spares_fixtures(self):
        dirty = self.scan("dirty.py")
        self.assertTrue(any(item["kind"] == "url" for item in dirty["hardcode"]))
        self.assertTrue(any(item["kind"].startswith("identifier") for item in dirty["language"]))
        fixture = self.scan("system/tests/test_fixture.py")
        self.assertEqual(fixture["hardcode"], [])
        self.assertEqual(self.scan("clean.py")["total"], 0)

    def test_scan_reports_the_django_comment_tag(self):
        (self.repo / "note.html").write_text(
            "{% comment %}\nRacional de design.\n{% endcomment %}\n<main>ok</main>\n",
            encoding="utf-8",
        )
        run(["git", "add", "note.html"], self.repo)

        found = self.scan("note.html")

        self.assertEqual(len(found["comments"]), 1)

    def test_review_refuses_silence_and_accepts_prd_or_justification(self):
        self.clean("init", "--owner", "clean", "--baseline", self.baseline)
        self.assertNotEqual(self.clean("review", "--owner", "clean", "--path", "dirty.py", check=False).returncode, 0)
        total = self.scan("dirty.py")["total"]
        self.assertEqual(
            self.clean("review", "--owner", "clean", "--path", "dirty.py",
                       "--justified", str(total), check=False).returncode,
            0,
        )
        self.clean("finding", "--owner", "clean", "--path", "docs/prd/PRD-050-x.md", "--status", "found")
        self.assertEqual(
            self.clean("review", "--owner", "clean", "--path", "page.html",
                       "--prds", "docs/prd/PRD-050-x.md", check=False).returncode,
            0,
        )
        self.assertEqual(self.clean("review", "--owner", "clean", "--path", "clean.py").returncode, 0)

    def test_lease_is_private_to_this_lane_and_survives_a_dead_holder(self):
        self.clean("release", "--owner", "clean")
        self.clean("acquire", "--owner", "outro")
        self.assertNotEqual(
            self.clean("init", "--owner", "clean", "--baseline", self.baseline, check=False).returncode, 0
        )
        code_lane = json.loads((self.agent / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(code_lane["lease"]["owner"], "codex")
        state = pathlib.Path(self.clean("path").stdout.strip())
        payload = json.loads(state.read_text(encoding="utf-8"))
        payload["lease"]["heartbeat"] = time.time() - 3600
        state.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(self.clean("acquire", "--owner", "clean", check=False).returncode, 0)

    def test_changed_file_returns_to_the_queue_by_blob(self):
        self.clean("init", "--owner", "clean", "--baseline", self.baseline)
        self.clean("review", "--owner", "clean", "--path", "clean.py")
        self.assertEqual(json.loads(self.clean("summary").stdout)["files_reviewed"], 1)
        (self.repo / "clean.py").write_text("value = 2\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "change"], self.repo)
        advanced = run(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.clean("init", "--owner", "clean", "--baseline", advanced)
        payload = json.loads(self.clean("summary").stdout)
        self.assertEqual(payload["files_reviewed"], 0)
        self.assertIn("clean.py", payload["next_pending"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
