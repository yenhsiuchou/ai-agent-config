#!/usr/bin/env python3
"""SessionStart and UserPromptSubmit hook: record which process runs each session.

A Claude Code process started for a new session does not show its session id
in its arguments, so a tool that asks "is this session still running?" cannot
tell from the process list alone. This hook walks up from itself to the
Claude Code process and records, per session id, that process's pid and start
time in `~/.claude/session-processes.json`:

    {"<session id>": {"pid": 123, "started": "<ps lstart>", "transcript": "<path>", "updated": 1700000000}}

A reader treats a session as running when its recorded pid is alive with the
same start time; the start time guards against a reused pid. Entries whose
process is gone for more than a week are dropped. The hook never blocks the
prompt: any failure exits 0 without output.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RECORD_PATH = Path("~/.claude/session-processes.json").expanduser()
KEEP_DEAD_S = 7 * 24 * 3600


def _ps(pid: int, field: str) -> str:
    return subprocess.run(["ps", "-o", f"{field}=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()


def process_started(pid: int) -> str:
    """The start time of a live process, or '' when it is gone."""
    return _ps(pid, "lstart")


def claude_ancestor() -> int | None:
    """The nearest ancestor process whose executable is named `claude`."""
    pid = os.getppid()
    for _ in range(8):
        if pid <= 1:
            return None
        if os.path.basename(_ps(pid, "comm")) == "claude":
            return pid
        parent = _ps(pid, "ppid")
        if not parent.isdigit():
            return None
        pid = int(parent)
    return None


def main() -> None:
    event = json.load(sys.stdin)
    session_id = event.get("session_id")
    pid = claude_ancestor()
    if not session_id or pid is None:
        return
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RECORD_PATH, "a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        try:
            records = json.loads(handle.read() or "{}")
        except json.JSONDecodeError:
            records = {}
        now = time.time()
        records = {
            sid: rec for sid, rec in records.items()
            if now - rec.get("updated", 0) < KEEP_DEAD_S or process_started(rec.get("pid", 0)) == rec.get("started")
        }
        records[session_id] = {
            "pid": pid,
            "started": process_started(pid),
            "transcript": event.get("transcript_path"),
            "updated": now,
        }
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(records, indent=1))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
