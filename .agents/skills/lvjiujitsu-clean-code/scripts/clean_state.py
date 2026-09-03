import argparse
import ast
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import tokenize
from datetime import datetime, timezone


SCHEMA_VERSION = 1
STALE_LEASE_SECONDS = 2700
CODE_SUFFIXES = {".py", ".js"}
MARKUP_SUFFIXES = {".html", ".css", ".svg", ".toml", ".yml", ".yaml"}
REVIEWABLE = CODE_SUFFIXES | MARKUP_SUFFIXES
PHASES = (
    "idle",
    "synchronizing",
    "reviewing",
    "prd",
    "implementing",
    "validating",
    "publishing",
    "cleanup",
    "pull_request",
    "blocked",
)
COMMENT_MARKERS = {
    ".html": ("<!--", "{#", "{% comment"),
    ".svg": ("<!--",),
    ".css": ("/*",),
    ".js": ("/*",),
    ".toml": ("#",),
    ".yml": ("#",),
    ".yaml": ("#",),
}
HARDCODE_PATTERNS = (
    ("url", re.compile(r"https?://(?!www\.w3\.org|localhost)[\w.-]+")),
    ("absolute_path", re.compile(r"[A-Za-z]:\\\\?[\w\\/.-]{4,}|(?<![\w.])/(?:home|Users|var|etc)/[\w/.-]+")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")),
    ("credential", re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[=:]\s*[\"'][^\"']{4,}")),
)
PORTUGUESE_WORDS = {
    "aluno",
    "arquivo",
    "assessoria",
    "botao",
    "cadastro",
    "cliente",
    "consulado",
    "dependente",
    "endereco",
    "erro",
    "estande",
    "expositor",
    "faixa",
    "graduacao",
    "mensagem",
    "mensalidade",
    "nome",
    "pagina",
    "parceiro",
    "passaporte",
    "presenca",
    "processo",
    "professor",
    "quantidade",
    "reserva",
    "senha",
    "situacao",
    "tela",
    "turma",
    "usuario",
    "valor",
    "viagem",
    "visto",
}
IDENTIFIER_PART = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")
ACCENTED = re.compile(r"[áàâãéêíóôõúüç]", re.IGNORECASE)
JAVASCRIPT_DECLARATION = re.compile(r"\b(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)")
ENGLISH_INTERFACE = re.compile(
    r"(?i)(?<![\w-])(save|cancel|delete|submit|search|close|loading|success|"
    r"warning|previous|password|username|edit|remove|confirm|yes|required|optional)(?![\w-])"
)
TAG_TEXT = re.compile(r">([^<>{}]{3,})<")


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def agent_directory() -> pathlib.Path:
    common = pathlib.Path(run("git", "rev-parse", "--git-common-dir")).resolve()
    return common / "lvjiujitsu-agent"


def repository_root() -> pathlib.Path:
    return pathlib.Path(run("git", "rev-parse", "--show-toplevel")).resolve()


def state_paths() -> tuple[pathlib.Path, pathlib.Path]:
    directory = agent_directory()
    return directory / "clean.json", directory / "clean.lock"


def lease_alive(lease: dict) -> bool:
    if lease.get("expires_at", 0) <= time.time():
        return False
    return lease.get("heartbeat", 0) > time.time() - STALE_LEASE_SECONDS


def acquire(data: dict, owner: str, ttl: int) -> None:
    lease = data.get("lease")
    if lease and lease.get("owner") != owner and lease_alive(lease):
        raise RuntimeError(f"Lease held by {lease['owner']}.")
    data["lease"] = {
        "acquired_at": now(),
        "expires_at": time.time() + ttl,
        "heartbeat": time.time(),
        "owner": owner,
    }


def require_lease(data: dict, owner: str) -> None:
    lease = data.get("lease")
    if not lease or lease.get("owner") != owner or lease.get("expires_at", 0) <= time.time():
        raise RuntimeError(f"Valid lease required for {owner}; acquire it first.")
    lease["heartbeat"] = time.time()


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        return {
            "baseline_sha": None,
            "feature": None,
            "files": {},
            "findings": {},
            "phase": "idle",
            "schema_version": SCHEMA_VERSION,
            "status": "clean_pending",
            "updated_at": now(),
            "worktree": None,
        }
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


class Lock:
    def __init__(self, path: pathlib.Path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.mkdir()
        except FileExistsError:
            if time.time() - self.path.stat().st_mtime <= 300:
                raise RuntimeError("Clean state write lock is active.")
            shutil.rmtree(self.path)
            self.path.mkdir()
        return self

    def __exit__(self, *_):
        self.path.rmdir()


def tracked_files(sha: str) -> dict[str, dict]:
    files = {}
    for line in run("git", "ls-tree", "-r", sha).splitlines():
        metadata, path = line.split("\t", 1)
        _, _, blob = metadata.split()
        if pathlib.PurePosixPath(path).suffix.lower() in REVIEWABLE:
            files[path] = {"blob": blob, "review": None, "status": "pending"}
    return files


def javascript_line_comment(line: str) -> bool:
    quote = None
    escaped = False
    for index in range(len(line) - 1):
        character = line[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote:
            if character == quote:
                quote = None
        elif character in ("'", '"', "`"):
            quote = character
        elif character == "/" and line[index + 1] == "/":
            return True
    return False


def python_comments(path: pathlib.Path) -> list[dict]:
    found = []
    with path.open("rb") as source:
        for token in tokenize.tokenize(source.readline):
            if token.type == tokenize.COMMENT:
                found.append({"line": token.start[0], "kind": "comment"})
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    nodes = [tree, *[n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]]
    for node in nodes:
        if ast.get_docstring(node, clean=False) is not None:
            found.append({"line": getattr(node, "lineno", 1), "kind": "docstring"})
    return found


def markup_comments(path: pathlib.Path, text: str) -> list[dict]:
    markers = COMMENT_MARKERS.get(path.suffix.lower(), ())
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if any(marker in stripped for marker in markers):
            found.append({"line": number, "kind": "comment"})
        elif path.suffix.lower() == ".js" and javascript_line_comment(line):
            found.append({"line": number, "kind": "comment"})
    return found


def python_identifiers(text: str, filename: str) -> list[tuple[int, str]]:
    tree = ast.parse(text, filename=filename)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append((node.lineno, node.name))
        elif isinstance(node, ast.arg):
            names.append((node.lineno, node.arg))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.append((node.lineno, node.id))
    return names


def identifier_parts(name: str) -> list[str]:
    parts = []
    for chunk in name.split("_"):
        parts.extend(IDENTIFIER_PART.findall(chunk))
    return [part.lower() for part in parts]


def suspect_identifier(name: str) -> str:
    if ACCENTED.search(name):
        return "identifier_accented"
    if any(part in PORTUGUESE_WORDS for part in identifier_parts(name)):
        return "identifier_portuguese"
    return ""


def scan_file(root: pathlib.Path, relative: str) -> dict:
    path = root / relative
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    comments = []
    if suffix == ".py" and "migrations" not in pathlib.PurePosixPath(relative).parts:
        comments = python_comments(path)
    elif suffix != ".py":
        comments = markup_comments(path, text)
    hardcode = []
    language = []
    if suffix == ".py":
        for line_number, name in python_identifiers(text, str(path)):
            kind = suspect_identifier(name)
            if kind:
                language.append({"line": line_number, "kind": kind, "excerpt": name[:40]})
    parts = pathlib.PurePosixPath(relative).parts
    fixture = "tests" in parts or pathlib.PurePosixPath(relative).name.startswith("test_")
    for number, line in enumerate(text.splitlines(), 1):
        if not fixture:
            for kind, pattern in HARDCODE_PATTERNS:
                match = pattern.search(line)
                if match:
                    hardcode.append({"line": number, "kind": kind, "excerpt": match.group(0)[:60]})
        if suffix == ".js":
            for name in JAVASCRIPT_DECLARATION.findall(line):
                kind = suspect_identifier(name)
                if kind:
                    language.append({"line": number, "kind": kind, "excerpt": name[:40]})
        if suffix in {".html", ".svg"}:
            for chunk in TAG_TEXT.findall(line):
                match = ENGLISH_INTERFACE.search(chunk)
                if match:
                    language.append({"line": number, "kind": "interface_english", "excerpt": match.group(0)[:40]})
                    break
    return {
        "comments": comments,
        "hardcode": hardcode[:40],
        "language": language[:40],
    }


def summary(data: dict) -> dict:
    files = data.get("files", {})
    pending = sorted(name for name, item in files.items() if item.get("status") != "reviewed")
    findings = data.get("findings", {})
    return {
        "baseline_sha": data.get("baseline_sha"),
        "feature": data.get("feature"),
        "files_pending": len(pending),
        "files_reviewed": len(files) - len(pending),
        "files_total": len(files),
        "findings_blocked": sorted(p for p, s in findings.items() if s == "blocked"),
        "findings_found": sorted(p for p, s in findings.items() if s == "found"),
        "findings_resolved": sum(1 for s in findings.values() if s == "resolved"),
        "next_pending": pending[:10],
        "phase": data.get("phase"),
        "schema_version": data.get("schema_version"),
        "status": data.get("status"),
        "worktree": data.get("worktree"),
    }


def initialize(data: dict, baseline: str) -> None:
    existing = data.get("files", {})
    incoming = tracked_files(baseline)
    settled = (
        data.get("status") == "clean_complete"
        and not data.get("feature")
        and not data.get("worktree")
        and all(status == "resolved" for status in data.get("findings", {}).values())
    )
    if data.get("baseline_sha") is None or settled:
        data["files"] = incoming
        data["status"] = "clean_pending"
    elif data.get("baseline_sha") != baseline:
        for path, item in incoming.items():
            previous = existing.get(path)
            if previous and previous["blob"] == item["blob"] and previous["status"] == "reviewed":
                incoming[path] = previous
        data["files"] = incoming
        data["status"] = "clean_pending"
    data["baseline_sha"] = baseline
    data["schema_version"] = SCHEMA_VERSION


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("path")
    sub.add_parser("summary")
    acquire_parser = sub.add_parser("acquire")
    acquire_parser.add_argument("--owner", required=True)
    acquire_parser.add_argument("--ttl", type=int, default=14400)
    release_parser = sub.add_parser("release")
    release_parser.add_argument("--owner", required=True)
    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("--path", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--owner", required=True)
    init_parser.add_argument("--baseline", required=True)
    review_parser = sub.add_parser("review")
    review_parser.add_argument("--owner", required=True)
    review_parser.add_argument("--path", required=True)
    review_parser.add_argument("--prds", nargs="*", default=[])
    review_parser.add_argument("--justified", type=int, default=0)
    finding_parser = sub.add_parser("finding")
    finding_parser.add_argument("--owner", required=True)
    finding_parser.add_argument("--path", required=True)
    finding_parser.add_argument("--status", choices=("found", "resolved", "blocked"), required=True)
    phase_parser = sub.add_parser("phase")
    phase_parser.add_argument("--owner", required=True)
    phase_parser.add_argument("--name", choices=PHASES, required=True)
    phase_parser.add_argument("--feature")
    phase_parser.add_argument("--worktree")
    complete_parser = sub.add_parser("complete-clean")
    complete_parser.add_argument("--owner", required=True)
    ready_parser = sub.add_parser("assert-ready")
    ready_parser.add_argument("--owner", required=True)
    cycle_parser = sub.add_parser("complete-cycle")
    cycle_parser.add_argument("--owner", required=True)
    args = parser.parse_args()
    state_path, lock_path = state_paths()
    if args.command == "path":
        print(state_path)
        return 0
    if args.command == "summary":
        print(json.dumps(summary(load(state_path)), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "scan":
        result = scan_file(repository_root(), args.path)
        result["path"] = args.path
        result["total"] = len(result["comments"]) + len(result["hardcode"]) + len(result["language"])
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    with Lock(lock_path):
        data = load(state_path)
        if args.command == "acquire":
            acquire(data, args.owner, args.ttl)
            save(state_path, data)
            print(json.dumps(summary(data), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        require_lease(data, args.owner)
        if args.command == "release":
            data["lease"] = None
        elif args.command == "init":
            initialize(data, args.baseline)
        elif args.command == "review":
            item = data["files"].get(args.path)
            if not item:
                raise RuntimeError("Path is not in the reviewable inventory.")
            result = scan_file(repository_root(), args.path)
            total = len(result["comments"]) + len(result["hardcode"]) + len(result["language"])
            unknown = sorted(set(args.prds) - set(data["findings"]))
            if unknown:
                raise RuntimeError(f"PRDs are not registered in the cycle: {unknown}.")
            if total and not args.prds and args.justified < total:
                raise RuntimeError(
                    f"Scan found {total} candidates in {args.path}; register a PRD or justify each one."
                )
            item["status"] = "reviewed"
            item["review"] = {
                "comments": len(result["comments"]),
                "hardcode": len(result["hardcode"]),
                "justified": args.justified,
                "language": len(result["language"]),
                "prds": sorted(set(args.prds)),
                "reviewed_at": now(),
            }
        elif args.command == "finding":
            data["findings"][args.path] = args.status
        elif args.command == "phase":
            data["phase"] = args.name
            if args.feature is not None:
                data["feature"] = args.feature
            if args.worktree is not None:
                data["worktree"] = args.worktree
        elif args.command == "complete-clean":
            pending = [n for n, i in data["files"].items() if i.get("status") != "reviewed"]
            if not data["files"]:
                raise RuntimeError("Reviewable inventory is empty.")
            if pending:
                raise RuntimeError(f"Clean coverage has {len(pending)} pending files.")
            data["status"] = "clean_complete"
        elif args.command == "assert-ready":
            if data["status"] != "clean_complete":
                raise RuntimeError("Clean coverage is not complete.")
            unresolved = [p for p, s in data["findings"].items() if s != "resolved"]
            if unresolved:
                raise RuntimeError(f"Cycle has {len(unresolved)} unresolved findings.")
        elif args.command == "complete-cycle":
            if data.get("worktree") and pathlib.Path(data["worktree"]).exists():
                raise RuntimeError("Cycle worktree still exists.")
            unresolved = [p for p, s in data["findings"].items() if s != "resolved"]
            if unresolved:
                raise RuntimeError(f"Cycle has {len(unresolved)} unresolved findings.")
            if data["status"] != "clean_complete":
                raise RuntimeError("Clean coverage is not complete.")
            data["phase"] = "idle"
            data["feature"] = None
            data["worktree"] = None
        save(state_path, data)
        print(json.dumps(summary(data), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, SyntaxError, subprocess.CalledProcessError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
