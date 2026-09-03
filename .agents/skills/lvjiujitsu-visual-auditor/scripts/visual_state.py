import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


SCHEMA_VERSION = 1
STALE_LEASE_SECONDS = 2700
VIEWPORTS = ("desktop", "mobile")
THEMES = ("light", "dark")
DESKTOP_MINIMUM_WIDTH = 1280
MOBILE_MAXIMUM_WIDTH = 430
ACCESS = ("public", "staff")
PHASES = (
    "idle",
    "synchronizing",
    "probing",
    "prd",
    "implementing",
    "validating",
    "publishing",
    "cleanup",
    "pull_request",
    "blocked",
)
NUMERIC_FIELDS = (
    "console_errors",
    "document_client_width",
    "document_scroll_width",
    "interactive_exercised",
    "interactive_total",
    "viewport_height",
    "viewport_width",
)
LIST_FIELDS = ("contrast_failures", "findings", "overlaps", "small_tap_targets")


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def agent_directory() -> pathlib.Path:
    common = pathlib.Path(run("git", "rev-parse", "--git-common-dir")).resolve()
    return common / "lvjiujitsu-agent"


def state_paths() -> tuple[pathlib.Path, pathlib.Path]:
    directory = agent_directory()
    return directory / "visual.json", directory / "visual.lock"


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
            "findings": {},
            "phase": "idle",
            "routes": {},
            "schema_version": SCHEMA_VERSION,
            "status": "visual_pending",
            "updated_at": now(),
            "worktree": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


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
                raise RuntimeError("Visual state write lock is active.")
            shutil.rmtree(self.path)
            self.path.mkdir()
        return self

    def __exit__(self, *_):
        self.path.rmdir()


def combinations() -> list[str]:
    return [f"{viewport}:{theme}" for viewport in VIEWPORTS for theme in THEMES]


def route_complete(route: dict) -> bool:
    probes = route.get("probes", {})
    return all(key in probes for key in combinations())


def evidence_file(state_path: pathlib.Path, value: str) -> pathlib.Path:
    path = pathlib.Path(value).resolve()
    root = (state_path.parent / "evidence").resolve()
    if path == root or root not in path.parents:
        raise RuntimeError("Report file is outside the agent evidence directory.")
    if not path.is_file() or path.stat().st_size <= 8:
        raise RuntimeError("Report file is absent or empty.")
    return path


def validate_report(path: pathlib.Path, viewport: str, theme: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not str(payload.get("url", "")).strip():
        raise RuntimeError("Report must record the inspected url.")
    if str(payload.get("theme", "")).strip() != theme:
        raise RuntimeError("Report theme differs from the recorded theme.")
    for field in NUMERIC_FIELDS:
        if not isinstance(payload.get(field), int):
            raise RuntimeError(f"Report must record {field} as an integer.")
    for field in LIST_FIELDS:
        if not isinstance(payload.get(field), list):
            raise RuntimeError(f"Report must record {field} as a list.")
    width = payload["viewport_width"]
    if viewport == "desktop" and width < DESKTOP_MINIMUM_WIDTH:
        raise RuntimeError("Desktop probe requires a desktop viewport width.")
    if viewport == "mobile" and width > MOBILE_MAXIMUM_WIDTH:
        raise RuntimeError("Mobile probe requires a mobile viewport width.")
    if payload["interactive_total"] < 0 or payload["interactive_exercised"] < 0:
        raise RuntimeError("Interactive counters must not be negative.")
    if payload["interactive_exercised"] != payload["interactive_total"]:
        raise RuntimeError(
            "Every interactive element must be exercised: "
            f"{payload['interactive_exercised']} of {payload['interactive_total']}."
        )
    measured = [
        payload["document_scroll_width"] > payload["document_client_width"],
        payload["console_errors"] > 0,
        bool(payload["small_tap_targets"]),
        bool(payload["contrast_failures"]),
        bool(payload["overlaps"]),
    ]
    if any(measured) and not payload["findings"]:
        raise RuntimeError("Measured defects require at least one finding in the report.")
    return payload


def summary(data: dict) -> dict:
    routes = data.get("routes", {})
    pending = sorted(name for name, route in routes.items() if not route_complete(route))
    findings = data.get("findings", {})
    return {
        "baseline_sha": data.get("baseline_sha"),
        "feature": data.get("feature"),
        "findings_blocked": sorted(p for p, s in findings.items() if s == "blocked"),
        "findings_found": sorted(p for p, s in findings.items() if s == "found"),
        "findings_resolved": sum(1 for s in findings.values() if s == "resolved"),
        "next_pending": pending[:10],
        "phase": data.get("phase"),
        "routes_complete": len(routes) - len(pending),
        "routes_pending": len(pending),
        "routes_total": len(routes),
        "schema_version": data.get("schema_version"),
        "status": data.get("status"),
        "worktree": data.get("worktree"),
    }


def initialize(data: dict, baseline: str, routes_file: str) -> None:
    entries = json.loads(pathlib.Path(routes_file).read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("Route inventory must be a non-empty list.")
    incoming = {}
    for entry in entries:
        name = str(entry.get("name", "")).strip()
        url = str(entry.get("url", "")).strip()
        access = str(entry.get("access", "")).strip()
        if not name or not url:
            raise RuntimeError("Each route requires name and url.")
        if access not in ACCESS:
            raise RuntimeError(f"Route access must be one of {list(ACCESS)}.")
        incoming[name] = {"access": access, "probes": {}, "url": url}
    settled = (
        data.get("status") == "visual_complete"
        and not data.get("feature")
        and not data.get("worktree")
        and all(status == "resolved" for status in data.get("findings", {}).values())
    )
    if data.get("baseline_sha") is None or settled or data.get("baseline_sha") != baseline:
        data["routes"] = incoming
        data["status"] = "visual_pending"
    data["baseline_sha"] = baseline
    data["schema_version"] = SCHEMA_VERSION


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("path").set_defaults(read_only=True)
    sub.add_parser("summary").set_defaults(read_only=True)
    acquire_parser = sub.add_parser("acquire")
    acquire_parser.add_argument("--owner", required=True)
    acquire_parser.add_argument("--ttl", type=int, default=14400)
    release_parser = sub.add_parser("release")
    release_parser.add_argument("--owner", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--owner", required=True)
    init_parser.add_argument("--baseline", required=True)
    init_parser.add_argument("--routes", required=True)
    probe_parser = sub.add_parser("probe")
    probe_parser.add_argument("--owner", required=True)
    probe_parser.add_argument("--route", required=True)
    probe_parser.add_argument("--viewport", choices=VIEWPORTS, required=True)
    probe_parser.add_argument("--theme", choices=THEMES, required=True)
    probe_parser.add_argument("--report", required=True)
    finding_parser = sub.add_parser("finding")
    finding_parser.add_argument("--owner", required=True)
    finding_parser.add_argument("--path", required=True)
    finding_parser.add_argument("--status", choices=("found", "resolved", "blocked"), required=True)
    phase_parser = sub.add_parser("phase")
    phase_parser.add_argument("--owner", required=True)
    phase_parser.add_argument("--name", choices=PHASES, required=True)
    phase_parser.add_argument("--feature")
    phase_parser.add_argument("--worktree")
    complete_parser = sub.add_parser("complete-visual")
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
            initialize(data, args.baseline, args.routes)
        elif args.command == "probe":
            route = data["routes"].get(args.route)
            if not route:
                raise RuntimeError("Route is not in the inventory.")
            report = evidence_file(state_path, args.report)
            payload = validate_report(report, args.viewport, args.theme)
            if payload["url"] != route["url"]:
                raise RuntimeError(
                    "Report url does not match the route registered in the inventory: "
                    f"expected {route['url']!r}, got {payload['url']!r}."
                )
            route["probes"][f"{args.viewport}:{args.theme}"] = {
                "console_errors": payload["console_errors"],
                "findings": payload["findings"],
                "interactive_total": payload["interactive_total"],
                "probed_at": now(),
                "report": str(report),
                "url": payload["url"],
            }
        elif args.command == "finding":
            data["findings"][args.path] = args.status
        elif args.command == "phase":
            data["phase"] = args.name
            if args.feature is not None:
                data["feature"] = args.feature
            if args.worktree is not None:
                data["worktree"] = args.worktree
        elif args.command == "complete-visual":
            pending = [name for name, route in data["routes"].items() if not route_complete(route)]
            if not data["routes"]:
                raise RuntimeError("Route inventory is empty.")
            if pending:
                raise RuntimeError(f"Visual coverage has {len(pending)} pending routes.")
            measured = any(
                probe.get("findings")
                for route in data["routes"].values()
                for probe in route.get("probes", {}).values()
            )
            if measured and not data.get("findings"):
                raise RuntimeError(
                    "Probes measured objective findings but no PRD was registered "
                    "via the 'finding' command."
                )
            data["status"] = "visual_complete"
        elif args.command == "assert-ready":
            if data["status"] != "visual_complete":
                raise RuntimeError("Visual coverage is not complete.")
            unresolved = [p for p, s in data["findings"].items() if s != "resolved"]
            if unresolved:
                raise RuntimeError(f"Cycle has {len(unresolved)} unresolved findings.")
        elif args.command == "complete-cycle":
            if data.get("worktree") and pathlib.Path(data["worktree"]).exists():
                raise RuntimeError("Cycle worktree still exists.")
            unresolved = [p for p, s in data["findings"].items() if s != "resolved"]
            if unresolved:
                raise RuntimeError(f"Cycle has {len(unresolved)} unresolved findings.")
            if data["status"] != "visual_complete":
                raise RuntimeError("Visual coverage is not complete.")
            data["phase"] = "idle"
            data["feature"] = None
            data["worktree"] = None
        save(state_path, data)
        print(json.dumps(summary(data), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
