#!/usr/bin/env python3
"""UserPromptSubmit hook: start the session title with `[<PR number>]` when
the prompt asks for a review of a PR.

A prompt counts as a review request when it contains a review word (such as
`review` or a review skill name) and names a PR by URL, `#<number>`,
`PR <number>`, or a number right after a review slash command. The title
becomes `[<number>] <PR title>`, read with `gh pr view` and without leading tags
such as `[compiler]`; when `gh` gives no title, it is
`[<number>] Review PR <number>`. A title that already starts with
`[<number>]` is left unchanged, and an existing title without one gets the
prefix in front of it.
"""
import json
import re
import subprocess
import sys

REVIEW_WORD = re.compile(r"review|審查|審核|審閱", re.I)
PR_REFERENCES = [
    re.compile(r"/pull/(\d+)"),
    re.compile(r"\bPR\s*#?\s*(\d+)", re.I),
    re.compile(r"(?<![\w&])#(\d+)\b"),
    re.compile(r"^\s*/[\w:-]*review[\w:-]*\s+(?:\S+\s+)*?#?(\d+)\b", re.I),
]
NUMBERED_TITLE = re.compile(r"^\[\d+\]")
LEADING_TAGS = re.compile(r"^(\[[^\]]*\]\s*)+")


def find_pr_number(prompt: str) -> str | None:
    if not REVIEW_WORD.search(prompt):
        return None
    for pattern in PR_REFERENCES:
        match = pattern.search(prompt)
        if match:
            return match.group(1)
    return None


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


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    number = find_pr_number(payload.get("prompt") or "")
    if number is None:
        return
    current_title = (payload.get("session_title") or "").strip()
    if NUMBERED_TITLE.match(current_title):
        return
    if current_title:
        title = f"[{number}] {current_title}"
    else:
        pr_title = read_pr_title(number, payload.get("cwd"))
        title = f"[{number}] {pr_title or f'Review PR {number}'}"
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "sessionTitle": title,
            }
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
