#!/usr/bin/env python3
"""Reject private or employer content before it reaches this public repository.

Two rule sets apply:

- Generic rules, kept here: absolute home paths, credential formats, PR
  numbers, long commit hashes, and email addresses that the local config does
  not allow.
- Private rules, kept outside the repository in
  `~/.agent-config-local/public-content.txt`, because the words themselves are
  private. Each line is `deny <regex>` (matched case-insensitively) or
  `allow-email <address>`; a line starting with `#` is a comment. The check
  fails when this file is missing.

Modes:
  --staged            lines added in the index (pre-commit)
  --push              commits read from a pre-push hook's stdin: their added
                      lines, messages, and author and committer emails
  --tree [REV]        every file at REV (default HEAD)
  --history           every file version, message, and email in all refs
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path("~/.agent-config-local/public-content.txt").expanduser()
ZERO_SHA = "0" * 40

GENERIC_RULES = {
    "home path": r"/(?:Users|home)/[A-Za-z0-9._-]+/",
    "credential": r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-ant-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "PR number": r"(?<![\w&])#[0-9]{3,5}\b|/pull/[0-9]+",
    "commit hash": r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])[0-9a-f]{10,40}\b",
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALWAYS_ALLOWED_EMAILS = {"noreply@anthropic.com"}


def load_rules() -> tuple[list[tuple[str, re.Pattern]], set[str]]:
    if not CONFIG_PATH.exists():
        sys.exit(f"check-public-content: {CONFIG_PATH} is missing; the private rules cannot run.")
    rules = [(name, re.compile(pattern)) for name, pattern in GENERIC_RULES.items()]
    allowed = set(ALWAYS_ALLOWED_EMAILS)
    for number, raw in enumerate(CONFIG_PATH.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        kind, _, value = line.partition(" ")
        if kind == "deny":
            rules.append((f"private rule {number}", re.compile(value.strip(), re.IGNORECASE)))
        elif kind == "allow-email":
            allowed.add(value.strip().lower())
        else:
            sys.exit(f"check-public-content: {CONFIG_PATH}:{number}: expected 'deny' or 'allow-email'")
    return rules, allowed


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, errors="replace").stdout


def find(text: str, rules, allowed) -> list[tuple[str, str]]:
    hits = [(name, m.group(0)) for name, rule in rules for m in rule.finditer(text)]
    hits += [("email", m.group(0)) for m in EMAIL.finditer(text) if m.group(0).lower() not in allowed]
    return hits


def scan_lines(where: str, lines, rules, allowed, report) -> None:
    for number, line in lines:
        for name, match in find(line, rules, allowed):
            report(f"{where}:{number}: {name}: {match!r}")


def added_lines(diff: str):
    """Yield (path, line number, text) for each added line of a unified diff."""
    path, number = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            number = int(re.search(r"\+(\d+)", line).group(1))
        elif path and line.startswith("+"):
            yield path, number, line[1:]
            number += 1
        elif path and not line.startswith("-"):
            number += 1


def scan_diff(label: str, diff: str, rules, allowed, report) -> None:
    for path, number, text in added_lines(diff):
        scan_lines(f"{label}{path}", [(number, text)], rules, allowed, report)
        for name, match in find(path, rules, allowed):
            report(f"{label}{path}: file name: {name}: {match!r}")


def scan_commit(commit: str, rules, allowed, report, *, with_diff: bool) -> None:
    meta = git("show", "-s", "--format=%ae%n%ce%n%B", commit).split("\n", 2)
    for email in meta[:2]:
        if email.lower() not in allowed:
            report(f"{commit[:12]}: author or committer email: {email!r}")
    scan_lines(f"{commit[:12]} message", enumerate(meta[2].splitlines(), 1), rules, allowed, report)
    if with_diff:
        scan_diff(f"{commit[:12]} ", git("show", "--format=", "-U0", "--no-renames", commit), rules, allowed, report)


def pushed_commits(stdin_text: str) -> list[str]:
    commits: list[str] = []
    for line in stdin_text.splitlines():
        _, local_sha, _, remote_sha = line.split()
        if local_sha == ZERO_SHA:
            continue
        span = [local_sha, "--not", "--remotes"] if remote_sha == ZERO_SHA else [f"{remote_sha}..{local_sha}"]
        commits += git("rev-list", "--reverse", *span).split()
    return commits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--push", action="store_true")
    mode.add_argument("--tree", nargs="?", const="HEAD", metavar="REV")
    mode.add_argument("--history", action="store_true")
    args = parser.parse_args()

    rules, allowed = load_rules()
    findings: list[str] = []
    report = findings.append

    if args.staged:
        scan_diff("", git("diff", "--cached", "-U0", "--no-renames"), rules, allowed, report)
    elif args.push:
        for commit in pushed_commits(sys.stdin.read()):
            scan_commit(commit, rules, allowed, report, with_diff=True)
    elif args.tree:
        for name in git("ls-tree", "-r", "--name-only", args.tree).splitlines():
            text = git("show", f"{args.tree}:{name}")
            scan_lines(name, enumerate(text.splitlines(), 1), rules, allowed, report)
    else:
        for commit in git("rev-list", "--all").split():
            scan_commit(commit, rules, allowed, report, with_diff=False)
        for line in git("rev-list", "--all", "--objects").splitlines():
            sha, _, name = line.partition(" ")
            if name and git("cat-file", "-t", sha).strip() == "blob":
                scan_lines(f"blob {sha[:12]} {name}", enumerate(git("cat-file", "-p", sha).splitlines(), 1), rules, allowed, report)

    if findings:
        print("check-public-content: private or employer content found:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
