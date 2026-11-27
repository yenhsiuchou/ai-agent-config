#!/usr/bin/env python3
"""UserPromptSubmit hook: give a session a title that says what it works on.

| Session | Title | Detected by |
| --- | --- | --- |
| Design work on a project | `[design] <project title>` | the tag `[project:<id> design]` |
| Project manager | `[manager] <project title>` | the tag `[project:<id> manager]` |
| Work on one project item | `[<item label>] <project title>` | the tag `[project:<id> item:<item id>]` |
| Review of a PR, or of its comments, started from Work Hub | `[<number>] <PR title>` | the tag `[pr-review:<number>]`, which Work Hub's review buttons put in the prompt |

A project tag decides the title even when the prompt also names a PR, and it
replaces any earlier title. When the prompt has no tag and the session has no
`[...]` title yet, the hook looks for a tag in the session's earlier prompts,
so a session started before this rule gets its title on its next prompt. Without a tag, a title that already starts with a
`[...]` prefix is left alone, and other sessions keep the title Claude Code
gives them. A title that starts with `[<1 or 2 digits>]` came from an older
rule that mistook a word like "PR 1a" for a PR number; the hook drops that
prefix and titles the session again.

Project titles come from `<projects root>/<id>.project.yaml`. The projects root
is `projects_root` in `~/.agent-config-local/session-titles.json`; without it,
the title uses the project id.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PR_REVIEW_TAG = re.compile(r"\[pr-review:(\d+)\]")
PROJECT_TAG = re.compile(r"\[project:([A-Za-z0-9._-]+)\s+(manager|design|item:([A-Za-z0-9._-]+))\]")
MISTAKEN_PREFIX = re.compile(r"^\[\d{1,2}\]\s*")
TITLED = re.compile(r"^\[[^\]]+\]")
LEADING_TAGS = re.compile(r"^(\[[^\]]*\]\s*)+")
LOCAL_CONFIG = Path("~/.agent-config-local/session-titles.json").expanduser()


def find_pr_number(prompt: str) -> str | None:
    match = PR_REVIEW_TAG.search(prompt)
    return match.group(1) if match else None


def read_pr_title(number: str, cwd: str | None) -> str | None:
    try:
        result = subprocess.run(
            ["gh", "pr", "view", number, "--json", "title", "--jq", ".title"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    title = LEADING_TAGS.sub("", result.stdout.strip())
    return title if result.returncode == 0 and title else None


def read_project(project_id: str) -> tuple[str, dict[str, str]]:
    """The project's title and its item labels by item id; the id when the file is not found."""
    try:
        root = Path(json.loads(LOCAL_CONFIG.read_text())["projects_root"]).expanduser()
        text = (root / f"{project_id}.project.yaml").read_text()
    except (OSError, KeyError, json.JSONDecodeError):
        return project_id, {}
    title = re.search(r"^title:\s*\"?(.*?)\"?\s*$", text, re.M)
    labels = {}
    for block in re.split(r"^\s*- id:", text, flags=re.M)[1:]:
        item_id = block.split("\n", 1)[0].strip().strip("\"'")
        label = re.search(r"^\s*label:\s*\"?(.*?)\"?\s*$", block, re.M)
        if label:
            labels[item_id] = label.group(1)
    return (title.group(1) if title else project_id), labels


def earlier_tag(transcript_path: str | None) -> str | None:
    """The first project tag in a prompt the user typed earlier in this session."""
    if not transcript_path:
        return None
    try:
        with open(transcript_path, encoding="utf-8") as transcript:
            for line in transcript:
                if "[project:" not in line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "user" or entry.get("isSidechain") or entry.get("isMeta"):
                    continue
                content = (entry.get("message") or {}).get("content")
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
                match = PROJECT_TAG.search(content or "")
                if match:
                    return match.group(0)
    except OSError:
        return None
    return None


def project_title(prompt: str) -> str | None:
    match = PROJECT_TAG.search(prompt)
    if not match:
        return None
    project_id, role, item_id = match.groups()
    title, labels = read_project(project_id)
    if item_id:
        return f"[{labels.get(item_id, f'PR {item_id}')}] {title}"
    return f"[{role}] {title}"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    prompt = payload.get("prompt") or ""
    original = current = (payload.get("session_title") or "").strip()
    title = project_title(prompt)
    if title is None and (MISTAKEN_PREFIX.match(current) or not TITLED.match(current)):
        title = project_title(earlier_tag(payload.get("transcript_path")) or "")
    if title is None:
        mistaken = bool(MISTAKEN_PREFIX.match(current))
        if mistaken:
            current = MISTAKEN_PREFIX.sub("", current)
        elif TITLED.match(current):
            return
        number = find_pr_number(prompt)
        if number is not None:
            title = f"[{number}] {current or read_pr_title(number, payload.get('cwd')) or f'Review PR {number}'}"
        elif mistaken:
            title = current
    if not title or title == original:
        return
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": title}},
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
