#!/usr/bin/env python3
"""PreToolUse hook: ask the user before a Bash command writes a GitHub PR
review or comment.

It matches `gh pr review`, `gh pr comment`, `gh api` writes to review or
comment endpoints, and GraphQL mutations on reviews or comments. Reads (GET)
pass through without a prompt.
"""
import json
import re
import sys

COMMENT_ENDPOINT = re.compile(
    r"(pulls/(\d+|\{[^}]+\}|:\w+)/(reviews|comments)"
    r"|pulls/comments/\d+"
    r"|pulls/\d+/comments/\d+/replies"
    r"|issues/(\d+|\{[^}]+\}|:\w+)/comments"
    r"|issues/comments/\d+)"
)
WRITE_METHOD = re.compile(r"(-X|--method)[ =]?['\"]?(POST|PATCH|PUT|DELETE)", re.I)
READ_METHOD = re.compile(r"(-X|--method)[ =]?['\"]?GET", re.I)
BODY_FLAG = re.compile(r"(^|\s)(-f|-F|--field|--raw-field|--input)(\s|=)")
GRAPHQL_MUTATION = re.compile(
    r"mutation[\s\S]*(PullRequestReview|addComment|ReviewThread|updateIssueComment|deleteIssueComment)"
)


def is_review_write(command: str) -> bool:
    if re.search(r"\bgh\s+pr\s+(review|comment)\b", command):
        return True
    for segment in re.split(r"&&|\|\||;|\|", command):
        if not re.search(r"\bgh\s+api\b", segment):
            continue
        if re.search(r"\bgh\s+api\s+graphql\b", segment):
            if GRAPHQL_MUTATION.search(segment):
                return True
            continue
        if not COMMENT_ENDPOINT.search(segment):
            continue
        if WRITE_METHOD.search(segment):
            return True
        if BODY_FLAG.search(segment) and not READ_METHOD.search(segment):
            return True
    return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not is_review_write(command):
        return
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "This command posts, edits, or deletes a GitHub PR review "
                    "or comment. Confirm that you asked for it to be posted."
                ),
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
