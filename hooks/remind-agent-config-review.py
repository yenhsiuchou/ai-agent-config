#!/usr/bin/env python3
"""PostToolUse hook: after an edit to an agent config source, remind Claude to review it.

An agent config source is a path under an `editable` entry of
`~/.agent-config-local/agent-config-review.json`: rules, skills, hooks, hook
settings, or memory. After a Write or Edit of such a file, the hook adds
context that asks Claude to run the `agent-config-review` skill in `changed`
mode once the batch of edits is done. The mechanical findings of
`check_agent_config.py` for that file come with the reminder.

For Bash, the detection is best effort. A file counts as changed when it is a
redirect target (`>`, `>>`), an argument of `sed -i`, `tee`, `rm`, or
`truncate`, or the destination of `cp` or `mv`. Edits made inside a script
that the command runs are missed.

Each file is reminded once per session. Without the local config, or on any
unexpected input, the hook prints nothing and exits 0.
"""
import glob
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG = Path("~/.agent-config-local/agent-config-review.json").expanduser()
CHECKER = Path("~/.claude/skills/agent-config-review/check_agent_config.py").expanduser()
EDIT_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
ANY_ARGUMENT = {"tee", "rm", "truncate"}
LAST_ARGUMENT = {"cp", "mv"}
REDIRECTS = {">", ">>", "&>", "1>", "2>"}
SEPARATORS = {";", "&&", "||", "|", "&"}


def watched_roots() -> list[Path]:
    editable = json.loads(CONFIG.read_text()).get("editable", {})
    roots = []
    for patterns in editable.values() if isinstance(editable, dict) else []:
        for pattern in patterns if isinstance(patterns, list) else []:
            roots += [Path(m).resolve() for m in glob.glob(str(Path(pattern).expanduser()))]
    return roots


def to_path(token: str, cwd: str) -> Path:
    token = os.path.expandvars(token)
    return Path(cwd, os.path.expanduser(token)).resolve()


def bash_targets(command: str, cwd: str) -> list[Path]:
    """The files a Bash command writes, by the rules in the module docstring."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    targets, words = [], []

    def end_command() -> None:
        args = [w for w in words[1:] if not w.startswith("-")]
        name = os.path.basename(words[0]) if words else ""
        in_place = name == "sed" and any(w.startswith("-i") for w in words[1:])
        if name in ANY_ARGUMENT or in_place:
            targets.extend(args)
        elif name in LAST_ARGUMENT and len(args) >= 2:
            targets.append(args[-1])
        words.clear()

    redirect = False
    for token in tokens:
        if redirect:
            if not token.startswith("&") and token != "/dev/null":
                targets.append(token)
            redirect = False
        elif token in REDIRECTS or (token.endswith(">") and token.rstrip(">").isdigit()):
            redirect = True
        elif token in SEPARATORS:
            end_command()
        else:
            words.append(token)
    end_command()
    return [to_path(t, cwd) for t in targets]


def changed_paths(payload: dict, roots: list[Path]) -> list[Path]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    cwd = payload.get("cwd") or os.getcwd()
    if payload.get("tool_name") in EDIT_TOOLS:
        raw = tool_input.get("file_path") or tool_input.get("notebook_path")
        candidates = [to_path(raw, cwd)] if isinstance(raw, str) and raw else []
    elif payload.get("tool_name") == "Bash" and isinstance(tool_input.get("command"), str):
        candidates = bash_targets(tool_input["command"], cwd)
    else:
        return []
    return sorted({p for p in candidates if any(p == r or r in p.parents for r in roots)})


def not_yet_reminded(session_id: str, paths: list[Path]) -> list[Path]:
    key = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    seen_file = Path(tempfile.gettempdir()) / f"agent-config-review-{key}.json"
    try:
        seen = set(json.loads(seen_file.read_text()))
    except (OSError, ValueError, TypeError):
        seen = set()
    fresh = [p for p in paths if str(p) not in seen]
    if fresh:
        seen_file.write_text(json.dumps(sorted(seen | {str(p) for p in fresh})))
    return fresh


def mechanical_findings(paths: list[Path]) -> str:
    if not CHECKER.exists():
        return ""
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--only", *map(str, paths)],
        capture_output=True, text=True, timeout=8,
    )
    return result.stdout.strip()


def main() -> None:
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        return
    paths = changed_paths(payload, watched_roots())
    paths = not_yet_reminded(str(payload.get("session_id") or ""), paths)
    if not paths:
        return
    names = ", ".join(str(p) for p in paths)
    context = (
        f"You changed an agent config source: {names}. When this batch of edits is done, "
        "run the agent-config-review skill in changed mode on the changed files before you hand off."
    )
    try:
        findings = mechanical_findings(paths)
    except (OSError, subprocess.SubprocessError):
        findings = ""
    if findings:
        context += "\nMechanical findings now:\n" + findings
    json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
