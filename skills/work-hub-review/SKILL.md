---
name: work-hub-review
description: Review an uncommitted change to the user's Work Hub (the local dashboard server and page) for correctness - syntax checks, then a fresh reviewer that checks the diff against the Work Hub invariants - and fix the confirmed bugs in the change. Use when the remind-review-after-edit hook asks for it after an edit to Work Hub, or when the user asks to review a Work Hub change.
---

# Work Hub Review

Work Hub is one server, several Python modules, one large page, and a VS Code
extension. A change in one place often needs a matching change elsewhere, and
the running server hides some bugs until it restarts. This skill reviews the
current uncommitted change in the Work Hub repository.

## Setup

Read `root` from `~/.agent-config-local/work-hub.json`; that is the Work Hub
repository. When the file is missing, ask the user for the path.

The change under review is `git -C <root> diff HEAD` plus the untracked files
that git does not ignore. When both are empty, say there is nothing to review
and stop.

## Step 1: Mechanical checks

Run `python3 <this skill's directory>/check_work_hub.py`. It checks the syntax
of each changed `.py`, `.js`, and the inline scripts of each `.html`. Fix every
problem it reports before Step 2.

## Step 2: Fresh reviewer

Start one fresh subagent (general-purpose). Give it:

- the root path and the list of changed files;
- the instruction to read the diff itself (`git -C <root> diff HEAD`, and the
  untracked files) and the code around each hunk, including the callers of
  any changed function;
- the path of `references/invariants.md` in this skill, to check the diff
  against every rule the changed files touch;
- the task: find correctness bugs this change adds, and broken invariants.
  For each finding: file and line, the rule or the bug, and a concrete
  failure scenario (input or state, then the wrong result). No style
  comments. Report "none" when nothing survives.

Do not give it the purpose of the change or your own view of it. The review
must not be anchored on the author's reading.

## Step 3: Verify and fix

For each finding, read the code yourself and decide: confirmed, or not a bug
(with the reason). Then:

- Fix each confirmed bug that this change introduced, keeping the design
  principles; a smaller patch that breaks an invariant is not a fix.
- Do not fix a pre-existing bug outside the change; list it.
- Apply rule 6 and rule 13 of the invariants when the change needs them:
  restart the server and call the changed API, or rebuild the extension.
  When a restart would cut off a running job, ask first.
- After fixes, run Step 1 again.

## Report

Reply with a short table: finding, verdict (fixed / not a bug / pre-existing),
and one line each. Then say what was verified at runtime (restart, `curl`,
extension rebuild) and what was not.
