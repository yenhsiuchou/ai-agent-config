---
name: weekly-retro
description: Run one step of the weekly retro of the user's development and agent workflow - draft the week's frictions and experiment candidates from facts.json, apply the experiments the user chose, or discuss a draft. Use when a prompt starts with /weekly-retro draft|apply|discuss <week dir>, which the Work Hub Retro tab sends; not for project status or PR review.
---

# Weekly Retro

The Work Hub Retro tab runs a weekly retro of the user's development and agent
workflow: PRs, reviews, branches, Claude and Codex sessions, projects, and
memory. Meetings and other work are out of scope.

One retro is a week directory (`.../retros/2026-W48/`):

| File | Written by | Holds |
| ---- | ---------- | ----- |
| `facts.json` | `retro.py collect`, no LLM | what happened in the period, `metrics`, `signals`, `previous_experiments`, `missing` sources |
| `draft.json` | this skill, `draft` mode | frictions and experiment candidates |
| `decisions.json` | the Retro tab only | the user's verdicts and chosen experiments |
| `retro.md` | `retro.py close` | the closed record |

Never write `decisions.json` or `retro.md` directly. The user decides on the
page; the page owns those files. The `apply` mode records an applied
experiment only through `retro.py mark-applied` and closes the week only
through `retro.py close`.

The first argument selects the mode; the second is the week directory.

## draft

A non-interactive run: nobody answers questions. Read `facts.json` and write
`draft.json` in the week directory, then end with its path.

Read the facts first, then look deeper only where a signal needs it: a PR's
description (`gh pr view`), a session's transcript under `~/.claude/projects`,
a skill under the skills repository. Do not count or analyze how often the
user corrected the agent; that is not a measure here.

Write every text value in simple English. Keep each value to one or two
sentences.

Text values carry no PR numbers, commit hashes, or session ids: the page shows
them to the user, and bare numbers do not read. Name the thing instead: "PR
7a", "the main comm library session (11.6h)", "the same design session". Put the PR
numbers, commits, and session ids that back an entry in its `refs` list (and
the summary's in `summary_refs`); the page shows them on hover.

```json
{
  "summary": ["What the week mainly did, one bullet per thread", "The clearest pattern"],
  "summary_refs": ["#<PR number>", "<first 8 chars of a session id>"],
  "time": [{"area": "comm library PRs", "detail": "implementation, reviews, reviewer replies", "share": "about 40%", "evidence": "8 PRs merged; main session 11.6h", "refs": ["#<PR number>"]}],
  "previous_experiments": [{
    "id": "<the exact id from facts.previous_experiments>",
    "change": "...", "landing": "...", "target": "...", "measure": "...",
    "evidence": "the measure's actual number or fact, e.g. cycle_days_median 3.0 → 2.1",
    "suggestion": "keep | adjust | drop",
    "reason": "why this suggestion",
    "refs": []
  }],
  "frictions": [{"id": "f1", "title": "...", "evidence": "one sentence naming the problem, with one key number", "cost": "one sentence: what it cost", "refs": ["#<PR number>", "<first 8 chars of a session id>"]}],
  "candidates": [{
    "id": "c1",
    "change": "what exactly to change",
    "landing": "skill | claude-md | memory | hook | project | habit",
    "target": "the file or skill to change; empty for a habit",
    "measure": "how next week shows it worked, using facts.metrics keys where possible",
    "addresses": ["f1"],
    "refs": []
  }]
}
```

Rules:

- `previous_experiments` has exactly one entry per entry of
  `facts.previous_experiments`, with the same `id`. `keep` means the change
  stays and tracking ends; `adjust` means change it and check it again next
  week; `drop` means revert it.
- Every friction and every evidence value rests on a fact: a PR, a session, a
  metric value, or a project item, with its number or id in `refs`. A pattern
  with no fact behind it is not a friction.
- `time[].area` is a short title of a few words; `detail` adds what the area
  covered in a short phrase.
- A friction's `evidence` states the problem in one short sentence with at
  most one key number, and `cost` says what it cost in one short sentence. The
  rest of the evidence stays in `refs`; do not quote transcripts or list
  every number.
- At most 6 frictions, ordered by cost. Treat `facts.signals` as leads, not as
  frictions.
- 3 to 5 candidates. Each one is small enough to apply in one session and
  says how next week's facts would show it worked. Prefer changing an existing
  skill, tool, or rule over adding a new one.
- Do not propose again a change listed in `facts.rejected_candidates`: the
  user turned it down. Propose it again only when new facts make a stronger
  case, and then name the week it was turned down and the new fact.
- When `facts.missing` names a source, add a `summary` bullet saying what that hides.

## apply

A session that runs without the user: the user chose the experiments on the
page and does not review the edits. Read `draft.json` and `decisions.json`.
The work is:

- each experiment in `decisions.chosen` whose `landing` is not `habit`;
- each previous experiment the user marked `adjust` (change it as its new
  evidence suggests) or `drop` (revert it).

For each one, in turn:

1. Make the change where its landing lives (table below). Keep it to what the
   experiment says; follow the target's own style and rules.
2. Review your own diff before committing: it does what the experiment's
   `change` says, its `measure` can be read from next week's facts, it does
   not contradict other rules in the same file or in the skills it names, and
   it passes the repository's checks (for the skills repository, its
   public-content check). Fix what the review finds.
3. Commit it in that repository, one commit per experiment, without asking.
   Do not push.
4. Record it: `python3 ~/WorkSpace/Notes/tools/pr-triage/retro.py mark-applied <week> <id>`
   for a chosen experiment.

Stop and ask only when a step needs something the user must allow: running
`install.sh` (see `hook` below) or a project's rules (see `claude-md`). The
Retro tab shows this session's state and the experiments marked applied, so
the user follows progress there.

When every one is committed and marked, close the week:
`python3 ~/WorkSpace/Notes/tools/pr-triage/retro.py close <week>`. If an
experiment could not be applied, leave it unmarked, close the week anyway, and
say why; next week's retro then sees it as not applied. End with one line per
experiment: its id and what changed in which skill or file, in words (no
commit hashes), then the path of `retro.md`.

After the week is closed, run the `agent-config-review` skill in `full` mode.
The per-edit reviews check only the files an edit touched; this weekly pass
also catches references that went stale without an edit, such as a merged PR
or a deleted file, and changes made outside Claude. Commit its mechanical
fixes in the repository that owns each file; memory has no repository. Its
semantic conflicts are questions for the user:
list them after the experiment lines and leave them for the user to answer
in this session.

Where each landing lives:

| Landing | Where |
| ------- | ----- |
| `skill` | the skills repository (`~/WorkSpace/Notes/ai-agent-config/skills/`), the only source of the user's skills |
| `claude-md` | the user's global rules: `~/WorkSpace/Notes/ai-agent-config/AGENTS.md`. A project's rules (`.claude/CLAUDE.md` in a repository) change through that repository's PR flow; ask first. |
| `memory` | a memory file and its `MEMORY.md` line |
| `hook` | `ai-agent-config/hooks/` and `claude/settings-hooks.json`, installed by `install.sh`. Installing changes `~/.claude/settings.json`, which can stop running sessions: ask before running it. |
| `project` | a `*.project.yaml` under the projects root |


## discuss

An interactive session for questions about the draft. Read the week's files
and answer from the facts. Do not edit any file in the week directory; when
the discussion changes a verdict, the user records it on the page, and a
better draft comes from **Re-draft**.
