---
name: cross-agent-design-doc
description: Write a design document for a problem, then have a fresh Claude reviewer and Codex design-review it, exchange findings for at most three rounds, apply the accepted findings, and let both reviewers read the result once more. Use whenever the user asks to write a design document (design doc, 設計文件, design 文件), even without mentioning a review, and when the user asks for a cross-agent review of an existing design document; for a PR or a diff, use cross-agent-review.
---

# Cross-Agent Design Doc

The author writes a design document for the user. Two reviewers who did not
see the writing review it independently, then answer each other's findings
for at most three rounds. The author applies every finding both reviewers
accept, and both reviewers read the result once more. Only wording should be
left at that point.

```
Step 0 problem -> Step 1 write -> Step 2 two reviews -> Step 3 ledger
  -> Step 4 exchange (<= 3 rounds) -> Step 5 apply -> Step 6 final read
  -> Step 7 wording fixes, archive, report
```

The document is for the user: Chinese, more diagrams than text, and a recap
of the knowledge it builds on. Write it by `references/doc-style.md`. When the
user later wants an English version for a repository, write it with the
`reader-first-writing` skill and run its cold-reader check.

## Roles

| Role | Who | Does |
| ---- | --- | ---- |
| Author | The agent that runs this skill | Writes the document, runs the reviewers, keeps the ledger, edits the document. It writes no review and casts no vote. |
| Reviewer CL | Claude, started fresh | Reviews without editing the document or the repository; writes probe files only under `<run-dir>/probes/reviewer-CL/`. IDs `CL-1`, `CL-2`, … |
| Reviewer CX | Codex, started fresh | Reviews in a read-only sandbox; runs probes on existing files or on stdin. IDs `CX-1`, `CX-2`, … |

Start each reviewer call fresh, with only the rendered prompt; a reviewer
never sees the author's conversation.

| Author runs in | Reviewer CL | Reviewer CX |
| -------------- | ----------- | ----------- |
| Claude Code | Agent tool, `subagent_type: general-purpose`, not a fork | `codex exec` |
| Codex | `claude -p` | `codex exec` |

- For `codex exec` and `claude -p`, use the commands and failure checks in
  `../cross-agent-review/references/peer-commands.md`, with `<workdir>` set to
  the repository the document is about. Its Codex command runs through the
  stall watchdog `../cross-agent-review/scripts/run_codex.py`.
- Run Codex at the effort set in `~/.codex/config.toml` for round 0 and the
  final read. In exchange rounds, add `-c model_reasoning_effort=medium`:
  an exchange answer checks claims that already carry evidence.
- For the Agent tool, give the prompt
  `Read <run-dir>/prompt-<step>-claude.md and follow it. Your final message is the deliverable.`
  Save the agent's final message to the output file yourself.
- Run the two reviewers of a step in parallel when the step allows it, in the
  background when the harness supports it.

If a reviewer fails, times out, or cannot start, stop and report the error.
Ask whether to continue with one reviewer. Never write a review or an answer
in a reviewer's place.

A run takes tens of minutes. When the harness has a notification tool, such as
`PushNotification` in Claude Code, send one line when the run finishes or
stops to ask the user something.

## Run Directory

```
<scratchpad or ${TMPDIR:-/tmp}>/cross-agent-design-doc/<doc-slug>-<UTC yyyymmdd-HHMMSS>/
  target.md              # problem, document path, repository, local build
  doc-r0.md              # document sent to round 0
  doc-r1.md              # document after Step 5
  doc-final.md           # document after Step 7
  review-claude.md       # round 0
  review-codex.md
  round-<n>-claude.md    # exchange answers, n = 1..3
  round-<n>-codex.md
  final-claude.md        # final read
  final-codex.md
  prompt-*.md            # rendered prompts
  probes/                # probes the author built
  probes/reviewer-CL/    # probes reviewer CL built
  ledger.md
  report.md
```

Pass absolute paths to the reviewers. Reviewers read the snapshot `doc-r<n>.md`
in the run directory, not the live document.

Render each prompt with `../cross-agent-review/scripts/render_prompt.py`; it
fails when a `{{KEY}}` is left unfilled:

```bash
python3 <skill-dir>/../cross-agent-review/scripts/render_prompt.py \
  <skill-dir>/references/reviewer-prompt.md <run-dir>/prompt-review-codex.md \
  RUN_DIR=<run-dir> SKILL_DIR=<skill-dir> PREFIX=CX
```

| Template | Keys |
| -------- | ---- |
| `reviewer-prompt.md` | `RUN_DIR`, `SKILL_DIR`, `PREFIX` |
| `reviewer-exchange-prompt.md` | `RUN_DIR`, `SKILL_DIR`, `REVIEWER_NAME`, `PREFIX`, `ROUND`, `PREVIOUS_ROUND_FILES` |
| `final-pass-prompt.md` | `RUN_DIR`, `SKILL_DIR`, `PREFIX` |

Put any extra instruction in `target.md` or `ledger.md`, not in a rendered
prompt.

## Step 0: Pin the Problem

Write `target.md`:

- **Problem:** what goes wrong or is missing, and for which stage or user.
- **Constraints:** contracts, pipeline positions, and limits the design must
  keep. List only real constraints: hardware, external contracts, and stated
  global invariants. Existing code in this repository is not a constraint.
- **Success condition:** what is true when the design is done.
- **Scope:** what the document decides, and what it leaves out.
- **Document:** the path. The default is
  `~/WorkSpace/Notes/docs/<Name>.zh.md`.
- **Repository and local build:** the working directory, the build
  directories, and the environment needed to run the built tools, as in
  Step 1 of `cross-agent-review`. Write `none` when no usable build exists.

When the user's request does not give the problem, constraints, or success
condition, show these lines (at most five) to the user and ask before writing.
When it gives them, write them down and continue.

**Entry with an existing document:** when the user names a document to
review, record it in `target.md`, copy it to `doc-r0.md`, and start at Step 2.
When an earlier archive of the same document exists, list its `ledger.md` in
`target.md`; a reviewer raises a finding dropped there again only with new
evidence.

**Entry from `top-down-design`:** the document was decided level by level,
and the project file lists its decisions and `design_frozen` steps. Record in
`target.md` the project file, the scope note the caller gives (one level, or
the whole document for the final review), and that each decision is frozen.
A finding that would change a decision is a reopen request: give it the
status it earns, but in Step 5 move it to `待決定` with the decision id
instead of editing the decision, and list it in the report so the caller can
reopen the decision with the user.

## Step 1: Write the Document

1. Read the code, tests, and design documents the problem touches. Run the
   pipeline on a real input to get the IR the document shows.
1. Derive the design from the constraints in `target.md` first, as if the
   existing code could all change. Then compare it with the current code and
   fill `現狀落差`: one row per gap, each with one decision (fix first in a
   prerequisite PR, isolate behind one boundary as debt, or keep with a
   reason).
1. Write the document by `references/doc-style.md` and
   `references/doc-template.md`.
1. Give every factual claim its evidence in the text: a file:line, a test, or
   a command and its IR.
1. Run the self-check at the end of `references/doc-style.md`.
1. Fill the Principle Gate of `../system-design-review/references/design-principles.md` for each decision that changes the IR.
   Change a decision that breaks a principle before the review starts.
1. Copy the document to `doc-r0.md`.

## Step 2: Independent Reviews (Round 0)

Render `reviewer-prompt.md` for each reviewer and start both. Each reviewer
follows **Target: A Design Document** of the `system-design-review` skill and
writes findings in `references/doc-finding-format.md`.

Rerun a reviewer once, naming what is missing, when its output:

- does not use the finding format; or
- lacks `## Coverage`, or its Facts table, necessity table, Principle Gate
  tables, or style check; or
- reports no finding and has no `## Candidates not reported` list.

If the rerun fails the same check, stop as for a reviewer failure.

## Step 3: Build the Ledger

Write `ledger.md` as in Step 3 of `cross-agent-review`, with one row per
finding of both reviews:

| ID | Category | Current title | Raised by | Reached | CL | CX | Status |
| -- | -------- | ------------- | --------- | ------- | -- | -- | ------ |

- The raising reviewer's column starts as `raised`.
- **Reach check.** For each finding about code behavior whose Reached is
  `read` or `not built`, try to build its trigger as a probe under `probes/`
  and record the result below the table: `built` with the command and
  result, `rejected by <layer>`, or `cannot build` with why.
- Below the table, keep the current text of every revised finding, copied
  from the answer file that revised it, with that file's name.
- **Clarity rows skip the exchange.** Give every `Clarity` finding the status
  `author`. The author applies it in Step 5, and the final read checks that it
  landed. When two `Clarity` findings conflict, the author picks the one that
  changes the meaning less and records why.

The author copies reviewer text into the ledger and does not rewrite it.

## Step 4: Exchange Rounds (at most 3)

Each round: CX answers every open row with the rendered
`reviewer-exchange-prompt.md`, then CL answers after reading CX's answers.
Use the answers, the evidence rules, the status rules, the early stop, and the
`unresolved` rule after round 3 exactly as in Step 4 of `cross-agent-review`,
with CL and CX as its two agents. A reviewer raises no new finding in an
exchange round; it lists one under `Late findings`.

An exchange answer reuses the evidence already in the run: the ledger's reach
check, the reviews, and the probe outputs under `probes/`. A reviewer reruns
or builds a probe only to dispute a result or to check a claim that no
existing result covers.

## Step 4b: Principle Gate

Run the Principle Gate of Step 4b of `cross-agent-review` on every row that is
`accepted`, `unverified`, or `unresolved`, and on the late findings, before
any edit. Give the gate `doc-r0.md`, the two reviews, and the ledger. Save its
answer as `gate.md`, and update the rows by the same rules: a `gate-revised`
row uses the gate's Next step; a row with no Next step that keeps the
principles moves to `待決定` with the decision the gate names.

## Step 5: Apply the Findings

Edit the document; keep each edit to what the finding's accepted Next step
asks. Rewrite the affected text in place: replace a wrong sentence, merge a
missing case into the table or diagram it belongs to, and remove the text a
fix makes redundant. Do not append a paragraph or a table cell to explain a
fix. The review should not make the document longer than the findings
require; record the size of `doc-r0.md` and `doc-r1.md` in the ledger.

Shortening keeps every claim. When you cut or split a sentence or a table
cell, the shorter text states the same claim with the same scope and the same
evidence. For example, "no in-bounds access reaches the padding" is a narrower
claim than "the verifier blocks every out-of-bound access", and only the first
is true. Compare each shortened claim with its `doc-r0.md` text before Step 6.

| Status | Action |
| ------ | ------ |
| `author` (`Clarity`) | Apply the finding's Next step. |
| `gate-revised` | Apply the gate's Next step, and mark it `gate 修改，未經 exchange` in `## Review 紀錄`. |
| `accepted` | Apply the accepted text. For a `Design question` whose Next step is a check, run the check when you can and write its result into the document; otherwise move it to the open decisions. |
| `accepted` `Optional trade-off` | Apply the option the accepted text recommends. Without a recommendation, move it to the open decisions. |
| `unverified` | Build the probe the row names. Apply the finding when the probe confirms it; otherwise move it to the open decisions with the probe result. |
| `unresolved` | Move it to the open decisions: the question, each reviewer's strongest argument with its evidence, and the check that would decide it. |
| `dropped`, `merged` | No edit. |
| Late findings | Judge each one; record what you applied in the ledger. |

The open decisions are the `待決定` section of the document. Record in the
ledger, per row, the section each edit changed. After editing, rerun the
self-check of `doc-style.md` and copy the document to `doc-r1.md`.

## Step 6: Final Read

Render `final-pass-prompt.md` for each reviewer and start both, fresh. Each
reviewer checks that every applied finding landed as accepted, answers the
cold-reader questions of `reader-first-writing`, and lists wording points and
any substantive problem.

## Step 7: Finish

1. Apply the wording points and fix every finding the final read marks
   `wrong` or `missing`. When the two reviewers' wording points conflict,
   choose the one that changes the meaning less.
1. Resolve every phrase that a cold read had to guess: define it in `名詞`,
   replace it with the code name, or delete it. Split each sentence named as
   the hardest to read.
1. Do not start a fourth round. For each substantive problem from the final
   read:
   - When its Next step corrects text or evidence and leaves the design
     unchanged, apply it, and mark it `final read 後修改，未經 review` in
     `## Review 紀錄` and in the report.
   - Otherwise, add it to `待決定` and list it in the report; the user decides
     whether to run the skill again.
1. Fill `## Review 紀錄` of the document: rounds used, counts per status,
   open decisions, and the archive path. Copy the document to `doc-final.md`.
1. Archive the run to
   `${CROSS_AGENT_DESIGN_DOC_ARCHIVE:-~/WorkSpace/Notes/reviews/design-docs}/<doc-slug>/<UTC yyyymmdd-HHMM>/`:
   `target.md`, `ledger.md`, `gate.md`, `report.md`, every `doc-*.md`, `review-*.md`,
   `round-*.md`, and `final-*.md`, and the probe sources under 50 KB. Do not
   copy builds, logs, or prompts.
1. Write `report.md` and give the user, in their language:
   - the document path and its one-line conclusion;
   - what the review changed, one line per applied finding;
   - the open decisions;
   - substantive problems from the final read: those applied without review,
     and those left to the user;
   - the document size before and after the review;
   - the principle gate result of each row and each `gate-revised` Next step;
   - rounds used, reviewer reruns or failures, probes built, and the archive
     path.

Do not commit or push the document unless the user asks.

## Splitting Out a Sub-Design

When the work of one item of a tracked project needs its own design, write
that design as a separate document and a sub-project, so that each level has
its own progress graph. Progress lives in project files under the projects
root, never in a design document; the format is in the `project-manager`
skill.

1. Write the child document with this skill, as a new run. Its problem is the
   item's problem; its constraints include the parent design's decisions.
1. Create the child's project file under the projects root, with `doc`
   linking the child document, `parent` set to the parent project's id, and
   one item per PR of the child design.
1. In the parent project file, either change the item to
   `project: <child-id>`, or keep it with `state: cancelled`, a `note` that
   names the child, and add a new item with `project: <child-id>`. A
   dependency of the old item moves to the child item that needs it.
1. Run the project tool's `check` and `sync`, which regenerate both
   projects' management pages. Do not add progress to either design
   document.

## Record Decisions in the Project

When the design belongs to a tracked project, keep its project file in step
with the document, so the project UI shows where the design stands:

- Each decision of the document's open-decisions section is an entry under
  `decisions:`, with a one-sentence English `question`, and `choice` once
  there is one. `depends_on` names the decisions whose answer this one builds
  on.
- `status` follows the decision: `open` while it is researched, `proposed`
  when options or a recommendation wait for the user, `decided` once the user
  chooses (with `date`), and `superseded` when a later decision replaces it.
- Order the tree from the top down. `invariants:` holds the document's global
  rules; each decision has a `level` (`ownership`, then `contract`, then
  `mechanism`) and builds only on decisions at its level or above; a root
  decision names the invariants it `serves`.
- When a finding overturns a decided parent, set the parent to `reopened`;
  do not patch the child alone. After the parent is decided again, restate
  each descendant and update its `date`.
- Add the run's archive slug to `reviews:` the first time a review of the
  document is archived.
- Run the project tool's `check` after each change.

