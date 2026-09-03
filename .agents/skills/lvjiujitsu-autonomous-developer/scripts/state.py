import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


SCHEMA_VERSION = 2
INSPECTION_CHUNK_BYTES = 32768
STALE_LEASE_SECONDS = 2700
PRD_PATTERN = re.compile(r"PRD-(\d{3,})")
UI_VIEWPORTS = ("desktop", "mobile")
UI_THEMES = ("light", "dark")
UI_STATES = ("happy", "invalid", "error", "permission")


RESPONSIBILITIES = (
    "asset",
    "command",
    "configuration",
    "css",
    "documentation",
    "form",
    "javascript",
    "migration",
    "model",
    "seed",
    "selector",
    "service",
    "template",
    "test",
    "view",
)
RISKS = (
    "accessibility",
    "authentication",
    "authorization",
    "configuration",
    "csrf",
    "data",
    "none",
    "performance",
    "security",
    "structure",
    "test",
    "ui",
)
PHASES = (
    "idle",
    "synchronizing",
    "global_audit",
    "diff_audit",
    "prd",
    "implementing",
    "validating",
    "refreshing",
    "publishing",
    "cleanup",
    "pull_request",
    "blocked",
)


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def run_bytes(*args: str) -> bytes:
    return subprocess.run(args, check=True, capture_output=True).stdout


def state_paths() -> tuple[pathlib.Path, pathlib.Path]:
    common = pathlib.Path(run("git", "rev-parse", "--git-common-dir")).resolve()
    directory = common / "lvjiujitsu-agent"
    return directory / "state.json", directory / "write.lock"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "baseline_sha": None,
            "global_status": "global_pending",
            "files": {},
            "last_stage_sha": None,
            "phase": "idle",
            "feature": None,
            "worktree": None,
            "prds": {},
            "ui_gates": {},
            "ui_required": False,
            "lease": None,
            "updated_at": now(),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


class Lock:
    def __init__(self, path: pathlib.Path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.mkdir()
        except FileExistsError:
            age = time.time() - self.path.stat().st_mtime
            if age <= 300:
                raise RuntimeError("State write lock is active.")
            shutil.rmtree(self.path)
            self.path.mkdir()
        return self

    def __exit__(self, *_):
        self.path.rmdir()


def lease_alive(lease: dict) -> bool:
    if lease["expires_at"] <= time.time():
        return False
    return lease.get("heartbeat", 0) > time.time() - STALE_LEASE_SECONDS


def require_lease(data: dict, owner: str) -> None:
    lease = data.get("lease")
    if not lease or lease["owner"] != owner or lease["expires_at"] <= time.time():
        raise RuntimeError("Valid lease required.")
    lease["heartbeat"] = time.time()


def tree_files(sha: str) -> dict[str, dict]:
    output = run("git", "ls-tree", "-r", sha)
    files = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        _, kind, blob = metadata.split()
        files[path] = {"blob": blob, "kind": kind, "status": "pending", "evidence": None}
    return files


def is_ui_path(path: str) -> bool:
    value = pathlib.PurePosixPath(path)
    return value.suffix.lower() in {".html", ".css", ".js"} or value.parts[:1] in {
        ("templates",),
        ("static",),
    }


def inspection(blob: str, previous: dict | None) -> tuple[dict, str]:
    content = run_bytes("git", "cat-file", "blob", blob)
    digest = hashlib.sha256(content).hexdigest()
    byte_count = len(content)
    line_count = content.count(b"\n") + int(bool(content) and not content.endswith(b"\n"))
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        value = {
            "binary": True,
            "byte_count": byte_count,
            "chunks": 1,
            "complete": True,
            "content_sha256": digest,
            "line_count": None,
            "offset": byte_count,
        }
        return value, ""
    current = previous or {}
    offset = current.get("offset", 0)
    if offset < 0 or offset > byte_count:
        offset = 0
    end = min(offset + INSPECTION_CHUNK_BYTES, byte_count)
    chunk = ""
    while end > offset:
        try:
            chunk = content[offset:end].decode("utf-8")
            break
        except UnicodeDecodeError:
            end -= 1
    value = {
        "binary": False,
        "byte_count": byte_count,
        "chunks": current.get("chunks", 0) + int(offset < byte_count or byte_count == 0),
        "complete": end == byte_count,
        "content_sha256": digest,
        "line_count": line_count,
        "offset": end,
    }
    return value, chunk


DESKTOP_MINIMUM_WIDTH = 1280
MOBILE_MAXIMUM_WIDTH = 430
DOM_ASSERTION_FIELDS = ("selector", "property", "observed", "expected")
DOM_ASSERTION_MINIMUM = 3


def evidence_file(state_path: pathlib.Path, value: str) -> pathlib.Path:
    path = pathlib.Path(value).resolve()
    root = (state_path.parent / "evidence").resolve()
    if path == root or root not in path.parents:
        raise RuntimeError("Evidence file is outside the agent evidence directory.")
    if not path.is_file() or path.stat().st_size <= 8:
        raise RuntimeError("Evidence file is absent or empty.")
    return path


def validate_dom_report(path: pathlib.Path, viewport: str, theme: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not str(payload.get("screenshot_error", "")).strip():
        raise RuntimeError("DOM evidence must record the screenshot failure it replaces.")
    if not str(payload.get("url", "")).strip():
        raise RuntimeError("DOM evidence must record the inspected url.")
    if str(payload.get("theme", "")).strip() != theme:
        raise RuntimeError("DOM evidence theme differs from the recorded theme.")
    width = payload.get("viewport_width")
    if not isinstance(width, int):
        raise RuntimeError("DOM evidence must record viewport_width as an integer.")
    if viewport == "desktop" and width < DESKTOP_MINIMUM_WIDTH:
        raise RuntimeError("Desktop evidence requires a desktop viewport width.")
    if viewport == "mobile" and width > MOBILE_MAXIMUM_WIDTH:
        raise RuntimeError("Mobile evidence requires a mobile viewport width.")
    assertions = payload.get("assertions")
    if not isinstance(assertions, list) or len(assertions) < DOM_ASSERTION_MINIMUM:
        raise RuntimeError(
            f"DOM evidence requires at least {DOM_ASSERTION_MINIMUM} concrete assertions."
        )
    for item in assertions:
        if not isinstance(item, dict):
            raise RuntimeError("Each DOM assertion must be an object.")
        missing = sorted(
            field for field in DOM_ASSERTION_FIELDS if not str(item.get(field, "")).strip()
        )
        if missing:
            raise RuntimeError(f"DOM assertion is missing fields: {missing}.")


def ui_gate_complete(gate: dict) -> bool:
    expected = {
        f"{viewport}:{theme}"
        for viewport in UI_VIEWPORTS
        for theme in UI_THEMES
    }
    evidence = gate.get("evidence", {})
    states = {
        state
        for item in evidence.values()
        for state in item.get("states", [])
    }
    return (
        expected <= set(evidence)
        and set(UI_STATES) <= states
        and all(
            item.get("console_errors") == 0
            and item.get("terminal_errors") == 0
            and (item.get("screenshot") or item.get("dom_report"))
            for item in evidence.values()
        )
    )


def summary(data: dict) -> dict:
    files = data.get("files", {})
    pending = sorted(path for path, item in files.items() if item.get("status") != "audited")
    prds = data.get("prds", {})
    gates = data.get("ui_gates", {})
    lease = data.get("lease")
    return {
        "baseline_sha": data.get("baseline_sha"),
        "feature": data.get("feature"),
        "files_audited": len(files) - len(pending),
        "files_pending": len(pending),
        "files_total": len(files),
        "global_status": data.get("global_status"),
        "lease_owner": lease["owner"] if lease else None,
        "lease_seconds_left": int(lease["expires_at"] - time.time()) if lease else None,
        "next_pending": pending[:10],
        "phase": data.get("phase"),
        "prds_blocked": sorted(path for path, status in prds.items() if status == "blocked"),
        "prds_found": sorted(path for path, status in prds.items() if status == "found"),
        "prds_dismissed": sum(1 for status in prds.values() if status == "dismissed"),
        "prds_resolved": sum(1 for status in prds.values() if status == "resolved"),
        "schema_version": data.get("schema_version"),
        "ui_gates_incomplete": sorted(
            scope for scope, gate in gates.items() if not ui_gate_complete(gate)
        ),
        "ui_visual_confirmation_pending": sorted(
            scope for scope, gate in gates.items() if gate.get("visual_confirmation_pending")
        ),
        "ui_required": data.get("ui_required"),
        "worktree": data.get("worktree"),
    }


def reserve_prd_numbers(owner: str, count: int) -> list[int]:
    if count < 1:
        raise RuntimeError("Reserve at least one PRD number.")
    directory = state_paths()[0].parent
    ledger = directory / "prd-reservations.json"
    directory.mkdir(parents=True, exist_ok=True)
    record = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else {}
    highest = 0
    for name in run("git", "ls-files", "docs/prd").splitlines():
        match = PRD_PATTERN.search(pathlib.PurePosixPath(name).name)
        if match:
            highest = max(highest, int(match.group(1)))
    for path in (pathlib.Path(run("git", "rev-parse", "--show-toplevel")) / "docs" / "prd").glob("*.md"):
        match = PRD_PATTERN.search(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    for numbers in record.values():
        highest = max([highest, *numbers])
    reserved = list(range(highest + 1, highest + 1 + count))
    record[f"{owner}:{now()}"] = reserved
    temporary = ledger.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, ledger)
    return reserved


def acquire(data: dict, owner: str, ttl: int) -> None:
    lease = data.get("lease")
    if lease and lease["owner"] != owner and lease_alive(lease):
        raise RuntimeError(f"Lease held by {lease['owner']}.")
    data["lease"] = {
        "acquired_at": now(),
        "expires_at": time.time() + ttl,
        "heartbeat": time.time(),
        "owner": owner,
    }


def initialize(data: dict, owner: str, baseline: str) -> None:
    require_lease(data, owner)
    current = data.get("baseline_sha")
    existing = data.get("files", {})
    incoming = tree_files(baseline)
    previous_schema = data.get("schema_version", 1)
    changed = {
        path
        for path, item in incoming.items()
        if path not in existing or existing[path]["blob"] != item["blob"]
    }
    settled = (
        data.get("global_status") == "global_complete"
        and not data.get("feature")
        and not data.get("worktree")
        and not any(status == "blocked" for status in data.get("prds", {}).values())
    )
    restart = current is None or previous_schema < SCHEMA_VERSION or settled
    if restart:
        data["files"] = incoming
        data["global_status"] = "global_pending"
        data["ui_gates"] = {}
        data["ui_required"] = any(is_ui_path(path) for path in incoming)
    elif current != baseline:
        for path, item in incoming.items():
            previous = existing.get(path)
            if (
                previous
                and previous["blob"] == item["blob"]
                and previous["status"] == "audited"
                and previous.get("inspection", {}).get("complete")
            ):
                incoming[path] = previous
        data["files"] = incoming
        data["global_status"] = "global_pending"
        data["ui_gates"] = {}
        data["ui_required"] = any(is_ui_path(path) for path in changed)
    data["schema_version"] = SCHEMA_VERSION
    data["baseline_sha"] = baseline


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    path_parser = sub.add_parser("path")
    path_parser.set_defaults(read_only=True)
    show_parser = sub.add_parser("show")
    show_parser.set_defaults(read_only=True)
    summary_parser = sub.add_parser("summary")
    summary_parser.set_defaults(read_only=True)
    acquire_parser = sub.add_parser("acquire")
    acquire_parser.add_argument("--owner", required=True)
    acquire_parser.add_argument("--ttl", type=int, default=14400)
    reserve_parser = sub.add_parser("prd-reserve")
    reserve_parser.add_argument("--owner", required=True)
    reserve_parser.add_argument("--count", type=int, default=1)
    reserve_parser.set_defaults(read_only=True)
    release_parser = sub.add_parser("release")
    release_parser.add_argument("--owner", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--owner", required=True)
    init_parser.add_argument("--baseline", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--owner", required=True)
    inspect_parser.add_argument("--path", required=True)
    audit_parser = sub.add_parser("audit")
    audit_parser.add_argument("--owner", required=True)
    audit_parser.add_argument("--path", required=True)
    audit_parser.add_argument("--responsibility", choices=RESPONSIBILITIES, required=True)
    audit_parser.add_argument("--consumers", nargs="*", default=[])
    audit_parser.add_argument("--risks", nargs="+", choices=RISKS, required=True)
    audit_parser.add_argument("--prds", nargs="*", default=[])
    invalidate_parser = sub.add_parser("invalidate")
    invalidate_parser.add_argument("--owner", required=True)
    invalidate_parser.add_argument("--path", required=True)
    phase_parser = sub.add_parser("phase")
    phase_parser.add_argument("--owner", required=True)
    phase_parser.add_argument("--name", choices=PHASES, required=True)
    phase_parser.add_argument("--feature")
    phase_parser.add_argument("--worktree")
    prd_parser = sub.add_parser("prd")
    prd_parser.add_argument("--owner", required=True)
    prd_parser.add_argument("--path", required=True)
    prd_parser.add_argument(
        "--status", choices=("found", "resolved", "blocked", "dismissed"), required=True
    )
    prd_parser.add_argument("--reason")
    ui_require_parser = sub.add_parser("ui-require")
    ui_require_parser.add_argument("--owner", required=True)
    ui_require_parser.add_argument("--prd", required=True)
    ui_evidence_parser = sub.add_parser("ui-evidence")
    ui_evidence_parser.add_argument("--owner", required=True)
    ui_evidence_parser.add_argument("--prd", required=True)
    ui_evidence_parser.add_argument("--route", required=True)
    ui_evidence_parser.add_argument("--viewport", choices=UI_VIEWPORTS, required=True)
    ui_evidence_parser.add_argument("--theme", choices=UI_THEMES, required=True)
    ui_evidence_parser.add_argument("--states", nargs="+", choices=UI_STATES, required=True)
    ui_evidence_parser.add_argument("--screenshot")
    ui_evidence_parser.add_argument("--dom-report")
    ui_evidence_parser.add_argument("--console-errors", type=int, required=True)
    ui_evidence_parser.add_argument("--terminal-errors", type=int, required=True)
    complete_parser = sub.add_parser("complete-global")
    complete_parser.add_argument("--owner", required=True)
    ready_parser = sub.add_parser("assert-ready")
    ready_parser.add_argument("--owner", required=True)
    reviewed_parser = sub.add_parser("stage-reviewed")
    reviewed_parser.add_argument("--owner", required=True)
    reviewed_parser.add_argument("--sha", required=True)
    complete_cycle_parser = sub.add_parser("complete-cycle")
    complete_cycle_parser.add_argument("--owner", required=True)
    complete_cycle_parser.add_argument("--stage-sha", required=True)
    args = parser.parse_args()
    state_path, lock_path = state_paths()
    if args.command == "path":
        print(state_path)
        return 0
    if args.command == "show":
        print(json.dumps(load(state_path), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "summary":
        print(json.dumps(summary(load(state_path)), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "prd-reserve":
        with Lock(state_path.parent / "prd.lock"):
            numbers = reserve_prd_numbers(args.owner, args.count)
        print(json.dumps({"owner": args.owner, "reserved": numbers}, sort_keys=True))
        return 0
    with Lock(lock_path):
        data = load(state_path)
        if args.command == "acquire":
            acquire(data, args.owner, args.ttl)
        elif args.command == "release":
            require_lease(data, args.owner)
            data["lease"] = None
        elif args.command == "init":
            initialize(data, args.owner, args.baseline)
        elif args.command == "inspect":
            require_lease(data, args.owner)
            item = data["files"].get(args.path)
            if not item:
                raise RuntimeError("Path is not in the baseline inventory.")
            value, content = inspection(item["blob"], item.get("inspection"))
            item["inspection"] = value
            print(
                json.dumps(
                    {
                        "action": "inspect",
                        "path": args.path,
                        "blob": item["blob"],
                        "binary": value["binary"],
                        "byte_count": value["byte_count"],
                        "line_count": value["line_count"],
                        "content_sha256": value["content_sha256"],
                        "offset": value["offset"],
                        "complete": value["complete"],
                        "content": content,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            save(state_path, data)
            return 0
        elif args.command == "audit":
            require_lease(data, args.owner)
            item = data["files"].get(args.path)
            if not item:
                raise RuntimeError("Path is not in the baseline inventory.")
            inspected = item.get("inspection", {})
            if not inspected.get("complete"):
                raise RuntimeError("Complete sequential inspection is required before audit.")
            unknown_consumers = sorted(set(args.consumers) - set(data["files"]))
            if unknown_consumers:
                raise RuntimeError(f"Consumers are outside the baseline inventory: {unknown_consumers}.")
            unknown_prds = sorted(set(args.prds) - set(data["prds"]))
            if unknown_prds:
                raise RuntimeError(f"PRDs are not registered in the cycle: {unknown_prds}.")
            risks = sorted(set(args.risks))
            if "none" in risks and len(risks) != 1:
                raise RuntimeError("Risk none cannot be combined with another risk.")
            item["status"] = "audited"
            item["evidence"] = {
                "audited_at": now(),
                "consumers": sorted(set(args.consumers)),
                "prds": sorted(set(args.prds)),
                "responsibility": args.responsibility,
                "risks": risks,
                "inspection": inspected,
            }
        elif args.command == "invalidate":
            require_lease(data, args.owner)
            item = data["files"].get(args.path)
            if not item:
                raise RuntimeError("Path is not in the baseline inventory.")
            item["status"] = "pending"
            item["evidence"] = None
            item["inspection"] = None
            data["global_status"] = "global_pending"
        elif args.command == "phase":
            require_lease(data, args.owner)
            data["phase"] = args.name
            if args.feature is not None:
                data["feature"] = args.feature
            if args.worktree is not None:
                data["worktree"] = args.worktree
        elif args.command == "prd":
            require_lease(data, args.owner)
            gate = data.get("ui_gates", {}).get(args.path)
            if args.status == "resolved" and gate and not ui_gate_complete(gate):
                raise RuntimeError("Complete browser evidence is required before resolving this PRD.")
            if args.status == "dismissed" and len(str(args.reason or "").strip()) < 40:
                raise RuntimeError(
                    "Dismissing a PRD requires --reason with the evidence that the defect does not exist."
                )
            data["prds"][args.path] = args.status
            if args.status == "dismissed":
                data.setdefault("dismissals", {})[args.path] = {
                    "at": now(),
                    "owner": args.owner,
                    "reason": args.reason.strip(),
                }
        elif args.command == "ui-require":
            require_lease(data, args.owner)
            data.setdefault("ui_gates", {}).setdefault(
                args.prd,
                {"required_at": now(), "evidence": {}},
            )
        elif args.command == "ui-evidence":
            require_lease(data, args.owner)
            gate = data.get("ui_gates", {}).get(args.prd)
            if not gate:
                raise RuntimeError("UI gate must be required before recording evidence.")
            if bool(args.screenshot) == bool(args.dom_report):
                raise RuntimeError("Record exactly one of --screenshot or --dom-report.")
            screenshot = None
            report = None
            if args.screenshot:
                screenshot = evidence_file(state_path, args.screenshot)
                if not screenshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError("Screenshot evidence is not a PNG file.")
            else:
                report = evidence_file(state_path, args.dom_report)
                validate_dom_report(report, args.viewport, args.theme)
            key = f"{args.viewport}:{args.theme}"
            gate["evidence"][key] = {
                "captured_at": now(),
                "console_errors": args.console_errors,
                "dom_report": str(report) if report else None,
                "route": args.route,
                "screenshot": str(screenshot) if screenshot else None,
                "states": sorted(set(args.states)),
                "terminal_errors": args.terminal_errors,
            }
            gate["complete"] = ui_gate_complete(gate)
            gate["visual_confirmation_pending"] = any(
                item.get("dom_report") for item in gate["evidence"].values()
            )
        elif args.command == "complete-global":
            require_lease(data, args.owner)
            pending = [path for path, item in data["files"].items() if item["status"] != "audited"]
            if pending:
                raise RuntimeError(f"Global audit has {len(pending)} pending files.")
            data["global_status"] = "global_complete"
        elif args.command == "assert-ready":
            require_lease(data, args.owner)
            blocked = [path for path, status in data["prds"].items() if status == "blocked"]
            if blocked:
                raise RuntimeError(f"Cycle has {len(blocked)} blocked PRDs.")
            if data["global_status"] != "global_complete":
                raise RuntimeError("Global audit is not complete.")
            gates = data.get("ui_gates", {})
            incomplete = [scope for scope, gate in gates.items() if not ui_gate_complete(gate)]
            if incomplete:
                raise RuntimeError(f"Cycle has {len(incomplete)} incomplete UI gates.")
            if data.get("ui_required") and not any(ui_gate_complete(gate) for gate in gates.values()):
                raise RuntimeError("Baseline UI changed and has no complete browser gate.")
        elif args.command == "stage-reviewed":
            require_lease(data, args.owner)
            data["last_stage_sha"] = args.sha
        elif args.command == "complete-cycle":
            require_lease(data, args.owner)
            worktree = data.get("worktree")
            feature = data.get("feature")
            if worktree and pathlib.Path(worktree).exists():
                raise RuntimeError("Cycle worktree still exists.")
            if feature and subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{feature}"],
                check=False,
            ).returncode == 0:
                raise RuntimeError("Cycle feature branch still exists.")
            blocked = [path for path, status in data["prds"].items() if status == "blocked"]
            if blocked:
                raise RuntimeError(f"Cycle has {len(blocked)} blocked PRDs.")
            if data["global_status"] != "global_complete":
                raise RuntimeError("Global audit is not complete.")
            gates = data.get("ui_gates", {})
            incomplete = [scope for scope, gate in gates.items() if not ui_gate_complete(gate)]
            if incomplete:
                raise RuntimeError(f"Cycle has {len(incomplete)} incomplete UI gates.")
            if data.get("ui_required") and not any(ui_gate_complete(gate) for gate in gates.values()):
                raise RuntimeError("Baseline UI changed and has no complete browser gate.")
            data["phase"] = "idle"
            data["feature"] = None
            data["worktree"] = None
            data["last_stage_sha"] = args.stage_sha
        save(state_path, data)
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
