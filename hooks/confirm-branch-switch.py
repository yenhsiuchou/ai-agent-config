#!/usr/bin/env python3
"""PreToolUse hook: ask the user before a Bash command switches branches in
a protected main checkout.

Other agents often work with uncommitted changes in a shared main checkout; a
branch switch there carries or blocks their changes. Branch work belongs in a
`git worktree`. The protected checkouts and the suggested worktree command
come from `~/.agent-config-local/branch-switch.json`:

    {"protected_checkouts": ["~/path/to/repo"],
     "worktree_hint": "git worktree add -b <branch> <dir> origin/main"}

Without that file the hook does nothing. The hook matches `git checkout` and `git switch` that change
the branch, including `-b`/`-c`. It lets through file restores
(`git checkout [<rev>] -- <path>`), `--help`, and any command whose
target directory is a linked worktree or another repository.
"""
import json
import os
import re
import shlex
import subprocess
import sys

LOCAL_CONFIG = os.path.expanduser("~/.agent-config-local/branch-switch.json")
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
GIT_OPTIONS_WITH_VALUE = {"-c", "--git-dir", "--work-tree", "--namespace"}


def load_config() -> tuple[set[str], str]:
    try:
        with open(LOCAL_CONFIG) as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set(), ""
    git_dirs = {
        os.path.realpath(os.path.join(os.path.expanduser(p), ".git"))
        for p in config.get("protected_checkouts") or []
    }
    return git_dirs, config.get("worktree_hint") or "git worktree add"


def is_protected_main_checkout(directory: str, protected: set[str]) -> bool:
    try:
        out = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--path-format=absolute",
             "--git-dir", "--git-common-dir"],
            capture_output=True, text=True, timeout=5,
        ).stdout.split()
    except (OSError, subprocess.TimeoutExpired):
        return False
    if len(out) != 2:
        return False
    git_dir, common_dir = (os.path.realpath(p) for p in out)
    return git_dir == common_dir and common_dir in protected


def switches_branch(subcommand: str, args: list[str]) -> bool:
    if not args or "-h" in args or "--help" in args:
        return False
    if subcommand == "checkout" and "--" in args:
        return False
    return True


def branch_switch_dirs(command: str, cwd: str) -> list[str]:
    """Return the directory of each segment that switches branches."""
    dirs = []
    current = cwd
    for segment in SEGMENT_SPLIT.split(command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            continue
        if not tokens:
            continue
        if tokens[0] == "cd" and len(tokens) >= 2:
            current = os.path.join(current, os.path.expanduser(tokens[1]))
            continue
        if os.path.basename(tokens[0]) != "git":
            continue
        directory = current
        i = 1
        while i < len(tokens) and tokens[i].startswith("-"):
            if tokens[i] == "-C" and i + 1 < len(tokens):
                directory = os.path.join(directory, os.path.expanduser(tokens[i + 1]))
                i += 2
            elif tokens[i] in GIT_OPTIONS_WITH_VALUE:
                i += 2
            else:
                i += 1
        if i < len(tokens) and tokens[i] in ("checkout", "switch"):
            if switches_branch(tokens[i], tokens[i + 1:]):
                dirs.append(directory)
    return dirs


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not re.search(r"\b(checkout|switch)\b", command):
        return
    protected, worktree_hint = load_config()
    if not protected:
        return
    cwd = payload.get("cwd") or os.getcwd()
    if not any(
        is_protected_main_checkout(d, protected)
        for d in branch_switch_dirs(command, cwd)
    ):
        return
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "This command switches branches in a shared main "
                    "checkout, where another agent may have uncommitted "
                    f"changes. Use `{worktree_hint}` instead; allow only if "
                    "you are sure the checkout is free."
                ),
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
