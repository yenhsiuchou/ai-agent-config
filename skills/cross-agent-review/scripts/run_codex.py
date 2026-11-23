#!/usr/bin/env python3
"""Run `codex exec` with a stall watchdog.

Usage:
  run_codex.py --prompt <prompt.md> --output <answer.md> --log <run.log>
               [--idle-timeout SECONDS] [--retries N] -- <codex exec arguments>

Runs `codex exec <arguments> -o <answer.md> -` with the prompt on stdin and
all output in the log. `codex exec` writes the log after each command and
each model response, so a log that does not grow for --idle-timeout seconds
(default 480) means a stalled request. The watchdog then kills the call and
starts it again from the prompt, up to --retries times (default 1).

Exit status: 0 when an attempt succeeds with a non-empty answer; the codex
exit status when it fails; 124 when every attempt stalls.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def descendants(pid):
    """Returns every process below pid; codex starts commands in new sessions."""
    table = subprocess.run(["ps", "-A", "-o", "pid=,ppid="],
                           capture_output=True, text=True).stdout
    children = {}
    for line in table.splitlines():
        child, parent = (int(x) for x in line.split())
        children.setdefault(parent, []).append(child)
    found, stack = [], [pid]
    while stack:
        for child in children.get(stack.pop(), []):
            found.append(child)
            stack.append(child)
    return found


def kill_tree(process):
    for pid in [process.pid, *descendants(process.pid)]:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()


def run_once(args, codex_args, attempt):
    log_path = Path(args.log)
    with log_path.open("a") as log:
        log.write(f"\n=== run_codex.py attempt {attempt} ===\n")
        log.flush()
        with open(args.prompt) as prompt:
            process = subprocess.Popen(
                ["codex", "exec", *codex_args, "-o", args.output, "-"],
                stdin=prompt, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        last_size = log_path.stat().st_size
        last_change = time.monotonic()
        while process.poll() is None:
            time.sleep(10)
            size = log_path.stat().st_size
            if size != last_size:
                last_size, last_change = size, time.monotonic()
            elif time.monotonic() - last_change > args.idle_timeout:
                kill_tree(process)
                log.write(f"\n=== run_codex.py: no output for "
                          f"{args.idle_timeout}s, killed attempt {attempt} ===\n")
                return None
        return process.returncode


def main(argv):
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--idle-timeout", type=int, default=480)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("codex_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    codex_args = args.codex_args[1:] if args.codex_args[:1] == ["--"] else args.codex_args

    for attempt in range(1, args.retries + 2):
        if os.path.exists(args.output):
            os.remove(args.output)
        status = run_once(args, codex_args, attempt)
        if status is None:
            print(f"attempt {attempt} stalled", file=sys.stderr)
            continue
        answered = os.path.exists(args.output) and os.path.getsize(args.output) > 0
        if status == 0 and answered:
            print(f"attempt {attempt} succeeded", file=sys.stderr)
            return 0
        print(f"codex exited {status}; see {args.log}", file=sys.stderr)
        return status or 1
    print(f"every attempt stalled; see {args.log}", file=sys.stderr)
    return 124


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
