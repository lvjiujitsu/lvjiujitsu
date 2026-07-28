import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_ROOT = ROOT / "static" / "system"
THEME_FILE = CSS_ROOT / "css" / "theme.css"
MARKUP_ROOTS = (ROOT / "templates", CSS_ROOT)
THEME_SELECTORS = {
    ":root",
    "html",
    ":root, html",
    'html[data-theme="light"]',
    'html[data-theme="dark"]',
    ':root, html[data-theme="light"]',
    ':root, html[data-theme="dark"]',
}
DECLARATION = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)")
USAGE = re.compile(r"var\(\s*(--[a-z0-9-]+)")
CUSTOM_PROPERTY = re.compile(r"(--[a-z0-9-]+)")


def rules(text):
    found = []
    index = 0
    while True:
        opening = text.find("{", index)
        if opening < 0:
            return found
        selector_start = max(text.rfind("}", 0, opening), text.rfind("{", 0, opening)) + 1
        selector = " ".join(text[selector_start:opening].split())
        depth, cursor = 1, opening + 1
        while cursor < len(text) and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        found.append((selector, text[opening + 1:cursor - 1], text[:opening].count("\n") + 1))
        index = opening + 1


def stylesheets():
    return sorted(CSS_ROOT.rglob("*.css"))


def inline_tokens():
    tokens = set()
    for root in MARKUP_ROOTS:
        if not root.exists():
            continue
        for path in list(root.rglob("*.html")) + list(root.rglob("*.js")):
            tokens.update(CUSTOM_PROPERTY.findall(path.read_text(encoding="utf-8", errors="replace")))
    return tokens


def audit():
    problems = []
    declared_anywhere = set()
    used_anywhere = set()
    theme_level = defaultdict(set)

    for path in stylesheets():
        relative = path.relative_to(CSS_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        used_anywhere.update(USAGE.findall(text))

        for selector, body, line in rules(text):
            if not body.strip():
                problems.append(f"bloco vazio: {relative}:{line} ({selector})")
            for token, value in DECLARATION.findall(body):
                declared_anywhere.add(token)
                if token in USAGE.findall(value):
                    problems.append(
                        f"propriedade autorreferente: {relative}:{line} {token}: {' '.join(value.split())}"
                    )
                if selector in THEME_SELECTORS:
                    theme_level[token].add(relative)

    if THEME_FILE.exists():
        core = {
            token
            for selector, body, _ in rules(THEME_FILE.read_text(encoding="utf-8"))
            if selector in THEME_SELECTORS
            for token, _ in DECLARATION.findall(body)
        }
        for token in sorted(core):
            owners = theme_level.get(token, set())
            if len(owners) > 1:
                problems.append(
                    f"token do nucleo declarado fora de theme.css: {token} <- {', '.join(sorted(owners))}"
                )
    else:
        problems.append(f"folha de tema ausente: {THEME_FILE.relative_to(ROOT).as_posix()}")

    positional = inline_tokens()
    for token in sorted(used_anywhere - declared_anywhere - positional):
        problems.append(f"token usado sem declaracao: {token}")

    return problems


def main():
    problems = audit()
    if not problems:
        print(f"[OK] {len(stylesheets())} folha(s) sem defeito de token.")
        return 0
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(problems)} defeito(s) de CSS.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
