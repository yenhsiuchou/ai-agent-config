#!/usr/bin/env python3
"""PreToolUse hook: ask the user before a tool call rewrites
~/.claude/settings.json while other Claude Code sessions are running.

Rewriting settings.json ends the Claude Code sessions running in VS Code. The
hook matches an Edit, Write, or MultiEdit of that file, a Bash command that
runs ai-agent-config's install.sh (which rewrites it), and a Bash command that
names the file together with a write such as `>`, `sed -i`, `mv`, or a script
interpreter.

Running sessions come from `~/.claude/session-processes.json`, which
record-session-process.py keeps: a session is running when its recorded pid is
alive with the same start time. The session that makes the call is left out.
With no other running session the hook prints nothing and the call goes on.
When the record cannot be read, the hook asks and says it could not check.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SETTINGS_PATH = Path("~/.claude/settings.json").expanduser()
RECORD_PATH = Path("~/.claude/session-processes.json").expanduser()
SETTINGS_NAME = re.compile(r"\.claude/settings\.json\b")
INSTALL_SCRIPT = re.compile(r"(ai-agent-config/install\.sh|(^|[\s;&|(])(\./)?install\.sh\b)")
WRITE_HINT = re.compile(
    r"(>{1,2}\s*\S*\.claude/settings\.json|\bsed\s+(-\w*\s+)*-i|\btee\b|\bmv\b|\bcp\b|\brm\b|\bln\b"
    r"|\bpython3?\b|\bnode\b|\bperl\b|\bjq\b[^|]*>)"
)
TITLE = re.compile(r'"customTitle":"((?:[^"\\]|\\.)*)"|"aiTitle":"((?:[^"\\]|\\.)*)"')


def is_settings_path(path: str, cwd: str) -> bool:
    if not path:
        return False
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = Path(cwd or ".") / target
    try:
        return target.resolve() == SETTINGS_PATH.resolve()
    except OSError:
        return False


def runs_install_script(command: str, cwd: str) -> bool:
    if "ai-agent-config/install.sh" in command:
        return True
    return bool(INSTALL_SCRIPT.search(command)) and Path(cwd or ".").name == "ai-agent-config"


def writes_settings(command: str) -> bool:
    for segment in re.split(r"&&|\|\||;", command):
        if SETTINGS_NAME.search(segment) and WRITE_HINT.search(segment):
            return True
    return False


def changes_settings(payload: dict) -> bool:
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or ""
    if payload.get("tool_name") in ("Edit", "Write", "MultiEdit"):
        return is_settings_path(tool_input.get("file_path") or "", cwd)
    if payload.get("tool_name") == "Bash":
        command = tool_input.get("command") or ""
        return runs_install_script(command, cwd) or writes_settings(command)
    return False


def process_started(pid: int) -> str:
    result = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True)
    return result.stdout.strip()


def session_title(transcript: str | None) -> str | None:
    """The newest custom or AI title recorded in a session's transcript."""
    if not transcript:
        return None
    try:
        text = Path(transcript).read_text(errors="replace")
    except OSError:
        return None
    titles = [custom or ai for custom, ai in TITLE.findall(text)]
    return json.loads(f'"{titles[-1]}"') if titles else None


def other_running_sessions(own_session: str | None) -> list[str]:
    records = json.loads(RECORD_PATH.read_text() or "{}")
    running = []
    for session_id, record in records.items():
        if session_id == own_session:
            continue
        pid = record.get("pid")
        if not isinstance(pid, int) or process_started(pid) != record.get("started"):
            continue
        title = session_title(record.get("transcript")) or "(untitled)"
        running.append(f"{title} — session {session_id[:8]}")
    return running


def ask(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    if not changes_settings(payload):
        return
    try:
        running = other_running_sessions(payload.get("session_id"))
    except (OSError, json.JSONDecodeError, AttributeError):
        ask(
            "This call rewrites ~/.claude/settings.json, which ends the Claude Code "
            "sessions running in VS Code. The running sessions could not be checked; "
            "confirm that none is running."
        )
        return
    if not running:
        return
    ask(
        "This call rewrites ~/.claude/settings.json, which ends these running "
        "Claude Code sessions:\n- " + "\n- ".join(running)
        + "\nAllow it only if they can be stopped now."
    )


if __name__ == "__main__":
    main()
