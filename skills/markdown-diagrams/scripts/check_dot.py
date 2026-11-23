#!/usr/bin/env python3
"""Render every ```dot block of Markdown files with Graphviz.

Usage:
  check_dot.py <file.md> [<file.md> ...]

Prints one line per block that Graphviz rejects, with the file, the line of
the opening fence, the nearest heading above it, and Graphviz's error.
Exits with status 1 when any block fails, 2 when Graphviz is not installed.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^```dot\s*(\{.*\})?\s*$")
HEADING = re.compile(r"^#{1,6}\s+(.*)$")


def dot_blocks(text: str):
    """Yields (line number of the opening fence, nearest heading, block source)."""
    heading = "(no heading)"
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = HEADING.match(line)
        if match:
            heading = match.group(1).strip()
        if FENCE_OPEN.match(line):
            start = i + 1
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            yield start, heading, "\n".join(body)
        i += 1


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    dot = shutil.which("dot")
    if dot is None:
        print("Graphviz `dot` is not installed", file=sys.stderr)
        return 2

    failures = 0
    checked = 0
    for name in argv:
        text = Path(name).read_text()
        for line, heading, source in dot_blocks(text):
            checked += 1
            result = subprocess.run(
                [dot, "-Tsvg", "-o", "/dev/null"],
                input=source, capture_output=True, text=True,
            )
            if result.returncode != 0:
                failures += 1
                error = result.stderr.strip().replace("\n", " | ")
                print(f"{name}:{line}: [{heading}] {error}")

    print(f"{checked} dot block(s) checked, {failures} failed", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
