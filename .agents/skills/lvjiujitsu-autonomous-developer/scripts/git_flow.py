import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time


def run(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def output(**values) -> None:
    print(json.dumps(values, ensure_ascii=False, sort_keys=True))


def root() -> pathlib.Path:
    return pathlib.Path(run(["git", "rev-parse", "--show-toplevel"], pathlib.Path.cwd()).stdout.strip()).resolve()


def sha(repo: pathlib.Path, ref: str) -> str:
    return run(["git", "rev-parse", ref], repo).stdout.strip()


def fetch(repo: pathlib.Path) -> None:
    run(["git", "fetch", "origin", "stage", "developer", "--prune"], repo)


FEATURE_PATTERN = re.compile(r"feature/prd-\d{3,}-[a-z0-9]+(?:-[a-z0-9]+)*")


def validate_feature(branch: str) -> None:
    if not FEATURE_PATTERN.fullmatch(branch):
        raise RuntimeError("Feature branch must match feature/prd-<number>-<slug>.")


def validate_worktree(repo: pathlib.Path, value: str) -> pathlib.Path:
    path = pathlib.Path(value).resolve()
    allowed = (repo / ".agents-runtime" / "worktrees").resolve()
    if path == allowed or allowed not in path.parents:
        raise RuntimeError("Worktree path is outside .agents-runtime/worktrees.")
    return path


def clean(path: pathlib.Path) -> bool:
    return not run(["git", "status", "--porcelain"], path).stdout.strip()


def commit(args, repo: pathlib.Path) -> None:
    validate_feature(args.branch)
    worktree = validate_worktree(repo, args.path)
    if not worktree.is_dir():
        raise RuntimeError("Worktree path does not exist.")
    current_branch = run(
        ["git", "branch", "--show-current"], worktree
    ).stdout.strip()
    if current_branch != args.branch:
        raise RuntimeError(
            f"Worktree branch differs: expected {args.branch}, found {current_branch}."
        )
    message = args.message.strip()
    if not message:
        raise RuntimeError("Commit message must not be empty.")
    status = run(["git", "status", "--porcelain"], worktree).stdout.splitlines()
    if not status:
        output(action="commit", state="clean", head=sha(worktree, "HEAD"))
        return
    if not args.execute:
        output(action="commit", state="required", changes=len(status))
        return
    run(["git", "add", "--all", "--", "."], worktree)
    if run(
        ["git", "diff", "--cached", "--quiet"], worktree, check=False
    ).returncode == 0:
        output(action="commit", state="clean", head=sha(worktree, "HEAD"))
        return
    run(["git", "commit", "-m", message], worktree)
    output(action="commit", state="committed", head=sha(worktree, "HEAD"))


def prepare(args, repo: pathlib.Path) -> None:
    validate_feature(args.branch)
    worktree = validate_worktree(repo, args.path)
    fetch(repo)
    stage = sha(repo, "origin/stage")
    developer = sha(repo, "origin/developer")
    if not args.execute:
        output(action="prepare", branch=args.branch, path=str(worktree), stage=stage, developer=developer)
        return
    if worktree.exists():
        raise RuntimeError("Worktree path already exists.")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{args.branch}"], repo, check=False).returncode == 0:
        raise RuntimeError("Feature branch already exists.")
    run(["git", "worktree", "add", "-b", args.branch, str(worktree), "origin/developer"], repo)
    merge = run(["git", "merge", "--no-edit", "origin/stage"], worktree, check=False)
    if merge.returncode != 0:
        output(action="prepare", state="conflict", branch=args.branch, path=str(worktree), stage=stage, developer=developer)
        raise RuntimeError("Stage merge has conflicts in the preserved worktree.")
    output(action="prepare", state="ready", branch=args.branch, path=str(worktree), stage=stage, developer=developer, head=sha(worktree, "HEAD"))


def sync(args, repo: pathlib.Path) -> None:
    fetch(repo)
    stage = sha(repo, "origin/stage")
    developer = sha(repo, "origin/developer")
    if stage == developer:
        output(action="sync", state="current", stage=stage, developer=developer)
        return
    if run(["git", "merge-base", "--is-ancestor", developer, stage], repo, check=False).returncode != 0:
        raise RuntimeError("Developer holds commits absent from stage; open the feature worktree to merge.")
    if not args.execute:
        output(action="sync", state="required", stage=stage, developer=developer)
        return
    run(["git", "push", "origin", f"{stage}:refs/heads/developer"], repo)
    fetch(repo)
    published = sha(repo, "origin/developer")
    if published != stage:
        raise RuntimeError("Remote developer did not reach the stage SHA.")
    output(action="sync", state="synchronized", stage=stage, developer=published)


GATE_COMMANDS = (
    ("check", ["manage.py", "check"]),
    ("migrations", ["manage.py", "makemigrations", "--check", "--dry-run"]),
    ("tests", ["manage.py", "test"]),
)


def receipt_path(repo: pathlib.Path) -> pathlib.Path:
    common = pathlib.Path(run(["git", "rev-parse", "--git-common-dir"], repo).stdout.strip()).resolve()
    return common / "lvjiujitsu-agent" / "gate-receipt.json"


def verify(args, repo: pathlib.Path) -> None:
    worktree = validate_worktree(repo, args.path)
    head = sha(worktree, "HEAD")
    interpreter = str(repo / ".venv" / "Scripts" / "python.exe")
    environment = dict(os.environ, DJANGO_ENV_FILE=str(repo / ".env"), PYTHONIOENCODING="utf-8")
    results = {}
    for name, command in GATE_COMMANDS:
        completed = subprocess.run(
            [interpreter, *command], cwd=worktree, capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=environment,
        )
        results[name] = completed.returncode
        if completed.returncode != 0:
            lines = (completed.stderr or completed.stdout or "").strip().splitlines()
            tail = [line[:200] for line in lines[-12:]]
            output(action="verify", state="failed", gate=name, head=head, detail=tail)
            raise RuntimeError(
                f"Gate {name} failed on {head[:7]}. Publication is blocked until the suite is green."
            )
    path = receipt_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"head": head, "gates": results, "verified_at": time.time()}, sort_keys=True),
        encoding="utf-8",
    )
    output(action="verify", state="green", head=head, gates=results)


def require_receipt(repo: pathlib.Path, head: str) -> None:
    path = receipt_path(repo)
    if not path.is_file():
        raise RuntimeError("No gate receipt found; run git_flow.py verify before publishing.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("head") != head:
        raise RuntimeError(
            f"Gate receipt is for {str(payload.get('head'))[:7]}, not {head[:7]}; run verify again."
        )
    if any(code != 0 for code in payload.get("gates", {}).values()):
        raise RuntimeError("Gate receipt records a failure; publication is blocked.")


def publish(args, repo: pathlib.Path) -> None:
    worktree = validate_worktree(repo, args.path)
    fetch(repo)
    remote = sha(repo, "origin/developer")
    head = sha(worktree, "HEAD")
    if remote != args.expected_developer:
        raise RuntimeError(f"Developer changed: expected {args.expected_developer}, found {remote}.")
    if not clean(worktree):
        raise RuntimeError("Worktree must be clean before publication.")
    if run(["git", "merge-base", "--is-ancestor", remote, head], worktree, check=False).returncode != 0:
        raise RuntimeError("Publication is not a fast-forward of origin/developer.")
    if run(["git", "merge-base", "--is-ancestor", "origin/stage", head], worktree, check=False).returncode != 0:
        raise RuntimeError("Publication does not contain the current origin/stage.")
    require_receipt(repo, head)
    if not args.execute:
        output(action="publish", developer=remote, head=head)
        return
    run(["git", "push", "origin", f"{head}:refs/heads/developer"], worktree)
    fetch(repo)
    published = sha(repo, "origin/developer")
    if published != head:
        raise RuntimeError("Remote developer did not reach the validated SHA.")
    output(action="publish", state="published", head=head)


def refresh(args, repo: pathlib.Path) -> None:
    worktree = validate_worktree(repo, args.path)
    if not clean(worktree):
        raise RuntimeError("Commit the feature before refreshing stage.")
    fetch(repo)
    before = sha(worktree, "HEAD")
    stage = sha(repo, "origin/stage")
    if run(["git", "merge-base", "--is-ancestor", stage, before], worktree, check=False).returncode == 0:
        output(action="refresh", state="current", stage=stage, head=before)
        return
    if not args.execute:
        output(action="refresh", state="required", stage=stage, head=before)
        return
    merge = run(["git", "merge", "--no-edit", "origin/stage"], worktree, check=False)
    if merge.returncode != 0:
        output(action="refresh", state="conflict", stage=stage, head=before)
        raise RuntimeError("Stage refresh has conflicts in the preserved worktree.")
    output(action="refresh", state="merged", stage=stage, head=sha(worktree, "HEAD"))


def cleanup(args, repo: pathlib.Path) -> None:
    validate_feature(args.branch)
    worktree = validate_worktree(repo, args.path)
    fetch(repo)
    if not clean(worktree):
        raise RuntimeError("Worktree is not clean.")
    if sha(worktree, "HEAD") != args.head:
        raise RuntimeError("Worktree HEAD differs from the cleanup SHA.")
    if run(["git", "merge-base", "--is-ancestor", args.head, "origin/developer"], repo, check=False).returncode != 0:
        raise RuntimeError("Cleanup SHA is not integrated in origin/developer.")
    if not args.execute:
        output(action="cleanup", branch=args.branch, path=str(worktree), head=args.head)
        return
    run(["git", "worktree", "remove", str(worktree)], repo)
    run(["git", "update-ref", "-d", f"refs/heads/{args.branch}", args.head], repo)
    output(action="cleanup", state="removed", branch=args.branch, path=str(worktree), head=args.head)


def gh_path() -> str:
    found = shutil.which("gh")
    fallback = pathlib.Path("C:/Program Files/GitHub CLI/gh.exe")
    if found:
        return found
    if fallback.is_file():
        return str(fallback)
    raise RuntimeError("GitHub CLI is unavailable.")


def ahead_count(repo: pathlib.Path) -> int:
    fetch(repo)
    return int(
        run(
            ["git", "rev-list", "--count", "origin/stage..origin/developer"],
            repo,
        ).stdout.strip()
    )


def required_check_state(payload: dict, expected_head: str, check_name: str) -> str:
    if payload.get("headRefOid") != expected_head:
        raise RuntimeError("Pull Request head differs from the validated SHA.")
    checks = [
        item
        for item in payload.get("statusCheckRollup") or []
        if item.get("name") == check_name
    ]
    if not checks:
        return "pending"
    check = checks[-1]
    if check.get("status") != "COMPLETED":
        return "pending"
    if check.get("conclusion") != "SUCCESS":
        raise RuntimeError(
            f"Required remote check failed: {check_name}={check.get('conclusion')}."
        )
    return "success"


def wait_for_check(
    gh: str,
    repo: pathlib.Path,
    number: str,
    expected_head: str,
    check_name: str,
    wait_seconds: int,
) -> dict:
    deadline = time.time() + wait_seconds
    while True:
        current = run(
            [
                gh,
                "pr",
                "view",
                number,
                "--json",
                "number,url,isDraft,headRefOid,statusCheckRollup",
            ],
            repo,
        )
        payload = json.loads(current.stdout)
        if required_check_state(payload, expected_head, check_name) == "success":
            return payload
        if time.time() >= deadline:
            raise RuntimeError(f"Required remote check did not complete: {check_name}.")
        time.sleep(10)


def pull_request(args, repo: pathlib.Path) -> None:
    ahead = ahead_count(repo)
    if ahead == 0:
        output(action="pull-request", state="no_changes", ahead=0)
        return
    gh = gh_path()
    query = run([gh, "pr", "list", "--head", "developer", "--base", "stage", "--state", "open", "--json", "number,url,isDraft"], repo)
    items = json.loads(query.stdout)
    if len(items) > 1:
        raise RuntimeError("More than one developer to stage Pull Request is open.")
    if not args.execute:
        output(action="pull-request", existing=items, ahead=ahead)
        return
    if items:
        number = str(items[0]["number"])
        run([gh, "pr", "edit", number, "--title", args.title, "--body-file", args.body_file], repo)
    else:
        created = run([gh, "pr", "create", "--base", "stage", "--head", "developer", "--draft", "--title", args.title, "--body-file", args.body_file], repo)
        number = created.stdout.strip()
    if args.ready:
        wait_for_check(
            gh,
            repo,
            number,
            args.head,
            args.check_name,
            args.wait_seconds,
        )
        current_state = run(
            [gh, "pr", "view", number, "--json", "isDraft"], repo
        )
        if json.loads(current_state.stdout)["isDraft"]:
            run([gh, "pr", "ready", number], repo)
    current = run([gh, "pr", "view", number, "--json", "number,url,isDraft,headRefOid,statusCheckRollup"], repo)
    print(current.stdout.strip())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--path", required=True)
    prepare_parser.add_argument("--branch", required=True)
    prepare_parser.add_argument("--execute", action="store_true")
    sync_parser = sub.add_parser("sync")
    sync_parser.add_argument("--execute", action="store_true")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--path", required=True)
    publish_parser = sub.add_parser("publish")
    publish_parser.add_argument("--path", required=True)
    publish_parser.add_argument("--expected-developer", required=True)
    publish_parser.add_argument("--execute", action="store_true")
    commit_parser = sub.add_parser("commit")
    commit_parser.add_argument("--path", required=True)
    commit_parser.add_argument("--branch", required=True)
    commit_parser.add_argument("--message", required=True)
    commit_parser.add_argument("--execute", action="store_true")
    refresh_parser = sub.add_parser("refresh")
    refresh_parser.add_argument("--path", required=True)
    refresh_parser.add_argument("--execute", action="store_true")
    cleanup_parser = sub.add_parser("cleanup")
    cleanup_parser.add_argument("--path", required=True)
    cleanup_parser.add_argument("--branch", required=True)
    cleanup_parser.add_argument("--head", required=True)
    cleanup_parser.add_argument("--execute", action="store_true")
    pr_parser = sub.add_parser("pull-request")
    pr_parser.add_argument("--title", required=True)
    pr_parser.add_argument("--body-file", required=True)
    pr_parser.add_argument("--ready", action="store_true")
    pr_parser.add_argument("--head", required=True)
    pr_parser.add_argument("--check-name", default="quality-gates")
    pr_parser.add_argument("--wait-seconds", type=int, default=1200)
    pr_parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    repo = root()
    if args.command == "prepare":
        prepare(args, repo)
    elif args.command == "commit":
        commit(args, repo)
    elif args.command == "sync":
        sync(args, repo)
    elif args.command == "verify":
        verify(args, repo)
    elif args.command == "publish":
        publish(args, repo)
    elif args.command == "refresh":
        refresh(args, repo)
    elif args.command == "cleanup":
        cleanup(args, repo)
    elif args.command == "pull-request":
        pull_request(args, repo)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
