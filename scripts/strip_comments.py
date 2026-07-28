import ast
import io
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__", "staticfiles", "node_modules", "migrations"}
APPLY = "--apply" in sys.argv


def walk(suffixes):
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in suffixes or not path.is_file():
            continue
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        yield path


def docstring_spans(tree):
    spans = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            continue
        alone = len(body) == 1 and not isinstance(node, ast.Module)
        spans.append((first.lineno, first.end_lineno, alone, first.col_offset))
    return spans


def strip_python(path):
    source = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return None, 0, f"nao parseia: linha {exc.lineno}"

    lines = source.splitlines(keepends=True)
    raw_lines = source.splitlines()
    drop, replace, removed = set(), {}, 0

    for start, end, alone, column in docstring_spans(tree):
        removed += 1
        if alone:
            replace[start - 1] = " " * column + "pass\n"
            drop.update(range(start, end))
        else:
            drop.update(range(start - 1, end))

    cuts = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            removed += 1
            row, column = token.start[0] - 1, token.start[1]
            if raw_lines[row][:column].strip():
                cuts[row] = min(cuts.get(row, column), column)
            else:
                drop.add(row)
    except tokenize.TokenError:
        return None, 0, "tokenize falhou"

    output = []
    for index, line in enumerate(lines):
        if index in replace:
            output.append(replace[index])
        elif index in drop:
            continue
        elif index in cuts:
            head = line[: cuts[index]].rstrip()
            if head:
                output.append(head + "\n")
        else:
            output.append(line)

    text = re.sub(r"\n{4,}", "\n\n\n", "".join(output))
    text = re.sub(r"\(\s*\n\s*\n", "(\n", text)
    try:
        compile(text, str(path), "exec")
    except SyntaxError as exc:
        return None, 0, f"resultado invalido: linha {exc.lineno}"
    return text, removed, None


def strip_web(path):
    source = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".html":
        count = len(re.findall(r"<!--(?!\[if)", source))
        text = re.sub(r"<!--(?!\[if).*?-->", "", source, flags=re.DOTALL)
    else:
        count = len(re.findall(r"/\*", source))
        text = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        kept = []
        for line in text.splitlines(keepends=True):
            if line.lstrip().startswith("//"):
                count += 1
                continue
            kept.append(line)
        text = "".join(kept)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text), count


def main():
    total, touched, failures = 0, [], []

    for path in walk({".py"}):
        text, removed, failure = strip_python(path)
        if failure:
            failures.append(f"{path.relative_to(ROOT).as_posix()}: {failure}")
            continue
        if removed:
            total += removed
            touched.append((path, text, removed))

    for path in walk({".css", ".js", ".html"}):
        text, removed = strip_web(path)
        if removed:
            total += removed
            touched.append((path, text, removed))

    for failure in failures:
        print(f"FALHA {failure}", file=sys.stderr)

    if not total:
        print(f"[OK] nenhum comentario ou docstring em {ROOT.name}.")
        return 1 if failures else 0

    for path, text, removed in touched:
        print(f"  {path.relative_to(ROOT).as_posix()}: {removed}", file=sys.stderr)
        if APPLY:
            path.write_text(text, encoding="utf-8", newline="\n")

    verb = "removido(s)" if APPLY else "encontrado(s), use --apply"
    print(f"{total} comentario(s)/docstring(s) {verb} em {len(touched)} arquivo(s).", file=sys.stderr)
    return 0 if APPLY and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
