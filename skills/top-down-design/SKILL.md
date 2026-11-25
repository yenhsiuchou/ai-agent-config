---
name: top-down-design
description: Design a new feature together with the user from the top down - frame the problem and invariants, then decide ownership, contracts, and mechanisms one level at a time, each decision chosen by the user from an option card and drawn on the Work Hub decision board, each level reviewed once and frozen before the next; teach a concept on the spot with direct-instruction when the user asks. Use when the user runs /top-down-design <project-id>, presses "Start top-down design" in Work Hub, or asks to design something new top-down; for a one-pass design document or the review of an existing document, use cross-agent-design-doc.
---

# Top-Down Design

The agent and the user design one feature together, one level at a time.
Each level answers its own questions, gets the user's choice for each
decision, is reviewed once, and is frozen. A lower level never changes a
frozen level; when it must, the higher level is reopened.

```
L0 Frame -> L1 Ownership -> L2 Contract -> L3 Mechanism -> L4 PR split -> Final review
 user        1 reviewer      Claude+Codex   1 reviewer      check          cross-agent-design-doc
 confirms    + gate          + gate                                        (whole document, once)
```

Talk to the user in Chinese; keep technical terms in English. Write the
project file in English.

## Inputs And State

- **Project:** `~/WorkSpace/Notes/projects/<project-id>.project.yaml`. Its
  format is in the `project-manager` skill. When the project does not exist,
  ask the user to create it in Work Hub (Projects → Add) and stop.
- **Tool:** `~/WorkSpace/Notes/tools/pr-triage/projects.py`. Run `check`
  after every edit of the project file; fix every error and every warning it
  prints for this project before you leave a level.
- **Document:** the project's `doc`. When it is `null`, propose
  `~/WorkSpace/Notes/docs/<Name>.zh.md`, write it from
  `references/doc-skeleton.md` once the user agrees, and set `doc` to its path
  relative to the project file.

All state lives in the document and the project file, so any session can
resume. The project file holds:

| Key | Holds |
| --- | --- |
| `invariants` | the global rules of L0 |
| `decisions` | every decision, with `level`, `status`, `choice`, `date`, `depends_on`, `serves`, `learn` |
| `design_frozen` | the steps already frozen: `frame`, `ownership`, `contract`, `mechanism`, `split` |
| `courses` | the direct-instruction courses of this design: `slug` and `dir` |
| `items` | the PRs of L4 |

**Resume.** The current step is the first step not in `design_frozen`. Tell
the user where the design stands: the frozen steps, the current step, the
decisions waiting for them. Work Hub shows the same thing on the project's
Design tab.

## The Loop Of One Level

`references/levels.md` lists what each level asks, what it writes into the
document, and when it may be left. Every level runs this loop:

1. **List the questions of this level only.** A question that belongs to a
   lower level goes to the document's `之後的層` section, not to the project
   file. Show the list to the user before you work on it.
1. **Gather facts.** Read the code; build probes when a fact is unknown. A
   probe is evidence for the decision that asked for it; record its command
   and result in the document.
1. **Write an option card per decision**, by `references/decision-card.md`.
   Add the decision to the project file with `status: proposed`, its `level`,
   `depends_on`, and `serves`. Work Hub now shows it on the board and under
   "Needs you".
1. **Ask the user.** Use AskUserQuestion, at most four decisions per call,
   ordered parent first. Each question offers the options of its card and the
   option "先教我 <concept>" (see Teaching). Record the choice: `status:
   decided`, `choice`, `date`. Write the decided design into the document's
   section of this level.
1. **Review this level** (table below). Apply findings to this level only. A
   finding against a frozen level is a reopen request: follow Reopen.
1. **Freeze.** Run `check`; when it is clean and the user agrees, add the step
   to `design_frozen`.

| Level | Review | How |
| --- | --- | --- |
| L0 Frame | the user | Show the problem, constraints, invariants, success condition, and scope; ask for confirmation. |
| L1 Ownership | one fresh Claude reviewer, then the principle gate | Agent tool, `subagent_type: general-purpose`, not a fork. Prompt: follow `system-design-review` **Target: A Design Document**, scoped to §1 by the scope note below. Then the gate of `../system-design-review/references/principle-gate-prompt.md` on every accepted finding. |
| L2 Contract | Claude and Codex | `cross-agent-design-doc`, entry from top-down-design: Step 0 with the scope note, Steps 2-5, archive as in Step 7. Skip its Step 6; the final review reads the whole document once. |
| L3 Mechanism | one fresh Claude reviewer | As L1, scoped to §3 and the path table. |
| L4 PR split | `projects.py check` and `sync` | One PR per contract boundary; see `levels.md`. |

The scope note, written into the reviewer's target or prompt:

> Review only <section>. The sections of the frozen levels are context: do not
> review their wording. When a finding shows that a frozen decision is wrong,
> report it as a reopen request that names the decision and its evidence.

Judge each finding of a single reviewer with evidence: apply it, or explain
to the user why not. A finding that changes a decision goes back to the user
as a new option card.

## Reopen

When anything shows that a decided decision of a higher level is wrong:

1. Stop the current level. Tell the user the decision and the evidence.
1. Set that decision to `status: reopened` and remove its level, and every
   level after it, from `design_frozen`. `check` now lists each decided
   descendant as "decided while ancestor ... is not; revalidate it".
1. Decide it again with an option card.
1. Walk down the tree: confirm or redecide each descendant, update its
   `date`, and fix the document. Do not patch a lower level to work around a
   higher decision.

## Teaching

The user may say "教我 X" at any time, or pick "先教我 <concept>" on a card.
At L0, list the concepts the design needs and ask which ones the user wants
taught.

1. Pause the level. Remember the decision being asked.
1. Run the `direct-instruction` skill in its **Called From A Design** mode:
   course directory `<doc dir>/<doc name without .zh.md>/course/`, slug = the
   project id with `-` replaced by `_`, goal = deciding that decision. Use the
   real IR and code of this design in the material.
1. Add the course to `courses` the first time. Add each chapter it wrote for a
   decision to that decision's `learn` list (path relative to the project
   file). Work Hub links the course and the chapter.
1. When the chapter is verified or the user says to continue, ask the paused
   decision again.

## Final Review And Finish

After L4 is frozen, run `cross-agent-design-doc` on the whole document,
entering with an existing document from top-down-design. Each finding
against a decision is a reopen request; handle it with Reopen. Then report to
the user:

- the one-line conclusion and the document path;
- the decision tree by level, and what the final review changed;
- the PR items and which one can start.

Do not commit or push anything unless the user asks.
