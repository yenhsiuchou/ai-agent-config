#!/usr/bin/env python3
"""Mechanical checks for a Work Hub change: syntax of every changed source file.

Usage: check_work_hub.py [ROOT]

ROOT defaults to `root` in `~/.agent-config-local/work-hub.json`. The changed
files are the tracked files that differ from HEAD plus the untracked files that
git does not ignore. Checks:

- `.py`: compiles with `py_compile` (written to a temporary directory, so no
  `__pycache__` is left behind).
- `.js`: `node --check`.
- `.html`: each inline `<script>` block (no `src`, no non-JavaScript `type`)
  is written to a temporary file and run through `node --check`; an error line
  is mapped back to the HTML line.

Prints one line per problem, `<path>:<line>: <message>`, and exits 1 when there
is any. When `node` is missing, the JavaScript checks report that once.
"""

from __future__ import annotations

import json
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG = Path("~/.agent-config-local/work-hub.json").expanduser()
SCRIPT_BLOCK = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.DOTALL | re.IGNORECASE)
JS_TYPES = {"", "text/javascript", "module", "application/javascript"}


def changed_files(root: Path) -> list[Path]:
    def git(*args: str) -> list[str]:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout
        return [line for line in out.splitlines() if line]

    names = set(git("diff", "--name-only", "HEAD")) | set(git("ls-files", "--others", "--exclude-standard"))
    return sorted(root / name for name in names if (root / name).is_file())


def check_python(path: Path, tmp: Path, report) -> None:
    try:
        py_compile.compile(str(path), cfile=str(tmp / "check.pyc"), doraise=True)
    except py_compile.PyCompileError as error:
        line = getattr(error.exc_value, "lineno", None) or 0
        report(path, line, error.exc_value if error.exc_value else error.msg)


def node_check(source: Path) -> tuple[int, str] | None:
    result = subprocess.run(["node", "--check", str(source)], capture_output=True, text=True)
    if result.returncode == 0:
        return None
    match = re.search(rf"{re.escape(str(source))}:(\d+)", result.stderr)
    message = next((l for l in result.stderr.splitlines() if "Error" in l), result.stderr.strip()[:200])
    return (int(match.group(1)) if match else 0, message)


def check_html(path: Path, tmp: Path, report) -> None:
    text = path.read_text()
    for index, block in enumerate(SCRIPT_BLOCK.finditer(text)):
        attrs = block.group("attrs")
        type_match = re.search(r'type\s*=\s*["\']?([^"\'\s>]+)', attrs)
        if "src=" in attrs or (type_match and type_match.group(1).lower() not in JS_TYPES):
            continue
        is_module = bool(type_match and type_match.group(1).lower() == "module")
        source = tmp / f"block{index}.{'mjs' if is_module else 'js'}"
        source.write_text(block.group("body"))
        problem = node_check(source)
        if problem:
            first_line = text.count("\n", 0, block.start("body")) + 1
            report(path, first_line + problem[0] - 1, problem[1])


def main() -> int:
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).expanduser().resolve()
    else:
        root = Path(json.loads(CONFIG.read_text())["root"]).expanduser().resolve()
    problems: list[str] = []

    def report(path: Path, line: int, message) -> None:
        problems.append(f"{path.relative_to(root)}:{line}: {message}")

    has_node = shutil.which("node") is not None
    files = changed_files(root)
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        for path in files:
            if path.suffix == ".py":
                check_python(path, tmp, report)
            elif path.suffix in {".js", ".html"} and not has_node:
                problems.append("node not found; JavaScript checks skipped")
                has_node = None
            elif path.suffix == ".js" and has_node:
                problem = node_check(path)
                if problem:
                    report(path, *problem)
            elif path.suffix == ".html" and has_node:
                check_html(path, tmp, report)

    print(f"checked {len(files)} changed file(s)")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
