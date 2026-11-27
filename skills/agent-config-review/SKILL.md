---
name: agent-config-review
description: Review the user's agent rules, memory, skills, and hooks against each other for conflicts, contradictions, duplicates, and stale references; fix mechanical problems directly and ask the user to settle each semantic conflict. Use when the user runs /agent-config-review [full | changed <path>...], asks to check that memory, skills, and hooks agree, or when a hook reminds you after editing one of them.
---

# Agent Config Review

The agent's behavior comes from several sources at once: global rules, memory,
skills, and hooks. Each is edited at a different time, so two sources can ask
for opposite behavior in the same situation. This skill finds those places and
makes the sources agree again.

## Setup

Read `~/.agent-config-local/agent-config-review.json`. It lists the sources by
kind, in two groups:

| Group | Meaning |
| ----- | ------- |
| `editable` | sources this skill may change |
| `read_only` | sources owned by others, such as a project's checked-in rules and skills; read them, never edit them |

When the file is missing, stop and ask the user which sources to cover.

## Modes

The first argument selects the mode. With no argument, run `full`.

- `full`: review every source against every other source.
- `changed <path>...`: review only the rules in the given files, each against
  every source. The `remind-review-after-edit` hook asks for this mode after
  an edit.

## Step 1: Mechanical Check

Run `python3 <this skill's directory>/check_agent_config.py`, with
`--only <path>...` in `changed` mode. Each output line is one finding:

| Check | Fix |
| ----- | --- |
| `memory-index-dangling`, `memory-index-missing` | make `MEMORY.md` list each memory file exactly once |
| `memory-frontmatter` | add the missing `name` or `description` from the file body |
| `memory-link-unresolved` | when a memory with another name holds that content, relink to it; otherwise leave it, since a link to an unwritten memory is allowed |
| `skill-name`, `skill-description` | fix the frontmatter |
| `skill-reference-unknown` | rename to the existing skill when the intent is clear; otherwise ask |
| `hook-script-not-installed` | run the owning repository's install script |
| `hook-script-missing`, `hook-script-unregistered`, `hook-settings-unreadable`, `hook-directory-missing` | register, restore, or remove so that settings and scripts match |
| `file-unreadable` | fix or remove the broken file or link |

Fix the findings in `editable` sources directly. Report a finding in a
`read_only` source; do not fix it.

## Step 2: Semantic Review

Read the sources in scope. In `full` mode that is every source; in `changed`
mode it is the changed files, plus every source that mentions the same
situation (search for the situation's words, the skill names, and the tools
it names).

Write each rule as one line:

```text
<situation> -> <required behavior>   (<source path>, <date when known>)
```

Example: `commit or push a PR branch -> show the user first and wait for
approval   (memory/show-before-commit-push.md, 2026-01-31)`.

Group the lines by situation, such as commit and push, PR text, review
comments, design decisions, language, diagrams, and teaching. Then look for:

| Kind | Example |
| ---- | ------- |
| Conflict | one rule says to ask first; another says to act without asking |
| Hook mismatch | a hook blocks or rewrites what a rule allows, or allows what a rule forbids |
| Overlap | two sources state the same rule; a later edit of one will make them differ |
| Stale | a rule names a file, skill, flag, PR state, or hook that no longer matches the current state |
| Scope gap | a rule's condition is broader or narrower than the behavior the user asked for, so it fires in the wrong cases |

Check a hook by reading its script: the events, the matched tools, and what it
blocks or rewrites. A hook's settings entry alone does not say what it does.

Before reporting that a rule is stale, check the current state: the file
exists or not, the skill is listed or not, the PR is merged or not.

## Step 3: Resolve

- Fix directly: overlap that only repeats a rule (keep one statement and link
  to it), stale references whose current value is certain, and the mechanical
  findings of step 1.
- Ask the user about every conflict, hook mismatch, and scope gap. There is no
  default precedence: newer does not win, and specific does not win. For each
  one, show the two rules with their sources and dates, the situation where
  they disagree, and two or three options. Each option names the files it
  changes.
- When a `read_only` source conflicts with an `editable` one, the options
  change only the `editable` source: align it with the read-only rule, or keep
  it and state the exception in that source.

After the user answers, apply the choices, then run `changed` mode once on the
files you edited. Stop after that pass and report anything left.

## Edits

- Memory: follow the memory format of the running agent; update `MEMORY.md`
  in the same step as the file.
- Skills, hooks, and global rules: edit them in the repository that owns them,
  never through an installed link. Run its install script after you add a skill
  or hook.
- When the owning repository is public, keep private names, paths, and
  project details out of it; put them in `~/.agent-config-local/`.

## Report

End with a short report in the user's reply language:

| Section | Holds |
| ------- | ----- |
| Fixed | each mechanical or overlap fix, with the file |
| Decided | each conflict the user settled, with the files changed |
| Open | read-only findings and anything not resolved |
