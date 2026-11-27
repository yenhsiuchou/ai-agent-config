#!/usr/bin/env python3
"""PostToolUse hook: after an edit to a watched file, remind Claude to review it.

Each watch maps a set of root paths to the review skill that covers them:

- Agent config sources: the paths under an `editable` entry of
  `~/.agent-config-local/agent-config-review.json` (rules, skills, hooks, hook
  settings, memory). The reminder asks for the `agent-config-review` skill in
  `changed` mode and carries the mechanical findings of
  `check_agent_config.py` for the changed files.
- Work Hub sources: the tree under `root` in
  `~/.agent-config-local/work-hub.json`, except its runtime directories
  (`data/`, `__pycache__/`, `.git/`). The reminder asks for the
  `work-hub-review` skill.

A watch whose local config is missing or unreadable watches nothing; the other
watches still run.

For Bash, the detection is best effort. A file counts as changed when it is a
redirect target (`>`, `>>`), an argument of `sed -i`, `tee`, `rm`, or
`truncate`, or the destination of `cp` or `mv`; sed's script is not a file.
A target that still holds `$` or a backtick after expanding the hook's own
environment, such as a variable the command itself sets, is skipped. Heredoc
bodies are input text, so a `>` inside one is not a redirect. Edits made
inside a script that the command runs are missed.

Each file is reminded once per session and watch. On any unexpected input, the
hook prints nothing and exits 0.
"""
import glob
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

AGENT_CONFIG = Path("~/.agent-config-local/agent-config-review.json").expanduser()
WORK_HUB_CONFIG = Path("~/.agent-config-local/work-hub.json").expanduser()
WORK_HUB_RUNTIME_DIRS = {"data", "__pycache__", ".git"}
CHECKER = Path("~/.claude/skills/agent-config-review/check_agent_config.py").expanduser()
EDIT_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
ANY_ARGUMENT = {"tee", "rm", "truncate"}
LAST_ARGUMENT = {"cp", "mv"}
REDIRECTS = {">", ">>", "&>", "1>", "2>"}
SEPARATORS = {";", "&&", "||", "|", "&"}
# `<<WORD`, `<<-WORD`, `<<'WORD'`, `<<"WORD"`; `<<<` is a here-string, not a heredoc.
HEREDOC_START = re.compile(r"(?<!<)<<(?!<)(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")


@dataclass
class Watch:
    name: str
    roots: list[Path]
    excluded_dirs: set[str]
    reminder: Callable[[list[Path]], str]

    def covers(self, path: Path) -> bool:
        for root in self.roots:
            if path == root or root in path.parents:
                relative = path.relative_to(root).parts
                return not (relative and relative[0] in self.excluded_dirs)
        return False


def expand_roots(patterns: list[str]) -> list[Path]:
    roots = []
    for pattern in patterns:
        roots += [Path(m).resolve() for m in glob.glob(str(Path(pattern).expanduser()))]
    return roots


def agent_config_watch() -> Watch:
    editable = json.loads(AGENT_CONFIG.read_text()).get("editable", {})
    patterns = [p for ps in editable.values() if isinstance(ps, list) for p in ps] if isinstance(editable, dict) else []

    def reminder(paths: list[Path]) -> str:
        text = (
            f"You changed an agent config source: {', '.join(map(str, paths))}. When this batch of edits "
            "is done, run the agent-config-review skill in changed mode on the changed files before you hand off."
        )
        try:
            findings = mechanical_findings(paths)
        except (OSError, subprocess.SubprocessError):
            findings = ""
        return text + ("\nMechanical findings now:\n" + findings if findings else "")

    return Watch("agent-config-review", expand_roots([p for p in patterns if isinstance(p, str)]), set(), reminder)


def work_hub_watch() -> Watch:
    root = json.loads(WORK_HUB_CONFIG.read_text()).get("root")

    def reminder(paths: list[Path]) -> str:
        return (
            f"You changed Work Hub source: {', '.join(map(str, paths))}. When this batch of edits is done, "
            "run the work-hub-review skill before you hand off."
        )

    return Watch("work-hub-review", expand_roots([root] if isinstance(root, str) else []), WORK_HUB_RUNTIME_DIRS, reminder)


def load_watches() -> list[Watch]:
    watches = []
    for build in (agent_config_watch, work_hub_watch):
        try:
            watches.append(build())
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    return watches


def to_path(token: str, cwd: str) -> Path | None:
    """The path a target names, or None when it uses a variable this hook cannot see."""
    token = os.path.expandvars(token)
    if "$" in token or "`" in token:
        return None
    return Path(cwd, os.path.expanduser(token)).resolve()


def sed_files(words: list[str]) -> list[str]:
    """The files a sed command edits: its operands, minus the script.

    The script is the value of -e or -f, or else the first operand. An empty
    word is the suffix of macOS `sed -i ''`.
    """
    operands, script_given, skip = [], False, False
    for word in words:
        if skip:
            skip = False
        elif word in ("-e", "-f", "--expression", "--file"):
            script_given = skip = True
        elif word.startswith(("-e", "-f", "--expression=", "--file=")):
            script_given = True
        elif word and not word.startswith("-"):
            operands.append(word)
    return operands if script_given else operands[1:]


def without_heredoc_bodies(command: str) -> str:
    """The command with each heredoc body removed; the line that opens it stays."""
    kept, pending = [], []
    for line in command.split("\n"):
        if pending:
            strip_tabs, word = pending[0]
            if (line.lstrip("\t") if strip_tabs else line) == word:
                pending.pop(0)
            continue
        kept.append(line)
        pending = [(dash == "-", word) for dash, _, word in HEREDOC_START.findall(line)]
    return "\n".join(kept)


def bash_targets(command: str, cwd: str) -> list[Path]:
    """The files a Bash command writes, by the rules in the module docstring."""
    try:
        lexer = shlex.shlex(without_heredoc_bodies(command), posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    targets, words = [], []

    def end_command() -> None:
        args = [w for w in words[1:] if w and not w.startswith("-")]
        name = os.path.basename(words[0]) if words else ""
        in_place = name == "sed" and any(w.startswith("-i") for w in words[1:])
        if in_place:
            targets.extend(sed_files(words[1:]))
        elif name in ANY_ARGUMENT:
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
    return [path for path in (to_path(t, cwd) for t in targets) if path is not None]


def changed_paths(payload: dict) -> list[Path]:
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
    return sorted(set(candidates))


def not_yet_reminded(session_id: str, watch_name: str, paths: list[Path]) -> list[Path]:
    key = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    seen_file = Path(tempfile.gettempdir()) / f"{watch_name}-{key}.json"
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
    changed = changed_paths(payload)
    if not changed:
        return
    session_id = str(payload.get("session_id") or "")
    reminders = []
    for watch in load_watches():
        paths = not_yet_reminded(session_id, watch.name, [p for p in changed if watch.covers(p)])
        if paths:
            reminders.append(watch.reminder(paths))
    if reminders:
        context = "\n\n".join(reminders)
        json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
