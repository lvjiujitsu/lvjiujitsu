import argparse
import ast
import json
import pathlib
import subprocess
import sys
import tokenize


TEXT_SUFFIXES = {".py", ".html", ".css", ".js"}
COMMENT_EXEMPT_FILES = {
    "asgi.py",
    "clear_migrations.py",
    "manage.py",
    "settings.py",
    "urls.py",
    "wsgi.py",
}


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def paths(all_files: bool, base: str) -> list[pathlib.Path]:
    command = (
        ("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        if all_files else ("git", "diff", "--name-only", "-z", base, "--")
    )
    return sorted({pathlib.Path(item) for item in run(*command).split("\0") if item and pathlib.Path(item).suffix in TEXT_SUFFIXES})


def python_findings(path: pathlib.Path) -> list[dict]:
    if "migrations" in path.parts:
        return []
    findings = []
    allows_comment = path.name in COMMENT_EXEMPT_FILES
    with path.open("rb") as source:
        for token in tokenize.tokenize(source.readline):
            if token.type == tokenize.COMMENT and not allows_comment:
                findings.append({"path": str(path), "line": token.start[0], "kind": "comment"})
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    nodes = [tree, *[node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]]
    for node in nodes:
        if ast.get_docstring(node, clean=False) is not None:
            findings.append({"path": str(path), "line": getattr(node, "lineno", 1), "kind": "docstring"})
    return findings


def markup_findings(path: pathlib.Path) -> list[dict]:
    findings = []
    text = path.read_text(encoding="utf-8-sig")
    markers = {".html": ("<!--", "{#", "{% comment"), ".css": ("/*",), ".js": ("/*",)}[path.suffix]
    code_block = path.suffix in (".css", ".js")
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if path.suffix == ".html":
            lowered = stripped.lower()
            if lowered.startswith("<script") or lowered.startswith("<style"):
                code_block = True
            elif lowered.startswith("</script") or lowered.startswith("</style"):
                code_block = False
        matched = False
        for marker in markers:
            if marker in stripped:
                findings.append({"path": str(path), "line": number, "kind": "comment"})
                matched = True
                break
        if matched:
            continue
        if code_block and ("/*" in stripped or javascript_line_comment(line)):
            findings.append({"path": str(path), "line": number, "kind": "comment"})
    return findings


def javascript_line_comment(line: str) -> bool:
    quote = None
    escaped = False
    index = 0
    while index < len(line) - 1:
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
        index += 1
    return False


def whitespace_findings(all_files: bool, base: str) -> list[dict]:
    commands = [
        ["git", "diff", "--check", "--"],
        ["git", "diff", "--cached", "--check", "--"],
    ]
    if not all_files:
        commands.append(["git", "diff", "--check", base, "--"])
    findings = []
    for command in commands:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode:
            findings.append(
                {
                    "path": "git-diff",
                    "line": 0,
                    "kind": "whitespace",
                    "detail": result.stdout or result.stderr,
                }
            )
    if all_files:
        for path in paths(True, base):
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if line.endswith((" ", "\t")):
                    findings.append(
                        {
                            "path": str(path),
                            "line": number,
                            "kind": "whitespace",
                            "detail": "trailing whitespace",
                        }
                    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--base", default="origin/developer")
    args = parser.parse_args()
    findings = []
    for path in paths(args.all, args.base):
        if not path.is_file():
            continue
        findings.extend(python_findings(path) if path.suffix == ".py" else markup_findings(path))
    findings.extend(whitespace_findings(args.all, args.base))
    print(json.dumps({"findings": findings}, ensure_ascii=True, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, SyntaxError, subprocess.CalledProcessError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
