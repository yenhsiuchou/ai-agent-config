---
name: cross-agent-review
description: Run a design review and a code review of one PR, commit, range, branch, or working-tree diff in both Claude and Codex, then exchange findings for at most three rounds and report the consensus and the remaining disagreements. Use when the user asks for a review by both Claude and Codex, a cross-agent or consensus review, or names this skill.
---

# Cross-Agent Review

Two agents review the same change independently. Then each agent reads the
other's findings and answers them, for at most three rounds. The result keeps
only findings that both agents accept and whose triggers were shown to reach
the code, and lists every remaining disagreement with both arguments.

Agreement alone does not make a finding real. Two agents can accept the same
wrong premise, such as an input that the IR verifier rejects. So every finding
states how its trigger was shown to exist (**Reached** in
`references/finding-format.md`), and the orchestrator builds the triggers the
peer cannot.

## Roles

- **Orchestrator:** the agent that runs this skill. It resolves the target,
  writes its own review, runs the peer, builds probes, and updates the ledger.
- **Peer:** the other agent, started as a non-interactive CLI process. It runs
  read-only: it can run the built tools on existing files or on stdin, but it
  cannot write a probe file or rebuild. Its other triggers are `read` or
  `not built` until the orchestrator checks them.

| Orchestrator | Peer command |
| ------------ | ------------ |
| Claude Code  | `codex exec` |
| Codex        | `claude -p`  |

Use the peer commands in `references/peer-commands.md`. The peer runs read-only
and returns its result as its final message; the orchestrator saves that
message to the run directory.

If the peer CLI is missing, fails to authenticate, or times out, stop. Report
the error and ask whether to continue with a single-agent review. Never write a
peer review or a peer answer yourself.

## Run Directory

Create one directory per run:

```
${TMPDIR:-/tmp}/cross-agent-review/<target-slug>-<UTC yyyymmdd-HHMMSS>/
  target.md               # resolved target and how to read and run it
  target.patch            # the reviewed diff
  review-claude.md        # independent review, round 0
  review-codex.md
  round-<n>-claude.md     # exchange answers, n = 1..3
  round-<n>-codex.md
  prompt-*.md             # rendered peer prompts
  ledger.md               # current status and text of every finding
  final.md                # consensus report
```

Use the scratchpad directory instead of `$TMPDIR` when the harness provides
one. Pass the absolute run-directory path to the peer.

The run directory is temporary; the system may clean it within days. Step 5
copies the review record to the archive, which a later follow-up review
reads:

```
${CROSS_AGENT_REVIEW_ARCHIVE:-~/WorkSpace/Notes/reviews}/<repo>/<key>/<UTC yyyymmdd-HHMM>-<head 8 chars>/
```

- `<repo>`: the base name of the repository's top-level directory.
- `<key>`: `pr<n>` for a PR; otherwise the branch name with each `/` replaced
  by `-`, such as `yenhsiuchou-fix-noc`.

## Rendering Peer Prompts

The prompt templates in `references/` use `{{KEY}}` placeholders. Render them
with the script; it fails when a placeholder is left unfilled:

```bash
python3 <skill-dir>/scripts/render_prompt.py \
  <skill-dir>/references/peer-exchange-prompt.md <run-dir>/prompt-round-2-codex.md \
  RUN_DIR=<run-dir> SKILL_DIR=<skill-dir> PEER_NAME=Codex PREFIX=CX ROUND=2 \
  "PREVIOUS_ROUND_FILES=<run-dir>/round-1-codex.md, <run-dir>/round-1-claude.md"
```

| Template                 | Keys                                                         |
| ------------------------ | ------------------------------------------------------------ |
| `peer-review-prompt.md`  | `RUN_DIR`, `SKILL_DIR`, `PREFIX`                             |
| `peer-exchange-prompt.md`| `RUN_DIR`, `SKILL_DIR`, `PEER_NAME`, `PREFIX`, `ROUND`, `PREVIOUS_ROUND_FILES` |

For round 1, set `PREVIOUS_ROUND_FILES=none (this is round 1)`. Put any extra
instruction in `target.md` or `ledger.md`, not in the rendered prompt.

## Step 1: Resolve the Target

Both agents must review the same code. Pin the target before either review
starts, and record it in `target.md`:

- **PR number or URL:** fetch `pull/<n>/head`, record the head SHA, and
  review `merge-base(origin/main, <sha>)..<sha>`. Record the PR title and
  description.
- **Commit, range, or branch:** resolve each end to a SHA. For a branch, use
  its merge base with `origin/main` unless the user gives a base.
- **Working tree:** record `HEAD` and save `git diff HEAD` (plus untracked
  files in scope) to `target.patch`. List untracked files that are out of
  scope. Do not edit the tree during the run.

Also record in `target.md`:

- the author's description, when the user gives one;
- **Author:** whether the orchestrator wrote the change in this session. When
  it did, its own review checks each assumption it made as author against the
  parameter-contract table, rather than taking the assumption as given;
- **Local build:** the build directories, the environment variables needed to
  import or run the built code, and whether the build includes the change
  (compare the build artifact time with the changed files). Use the
  repository's documented test environment, such as the variables that the
  project `AGENTS.md` lists for its tests. Write `none` when no usable build
  exists.
- **Probes:** how the orchestrator builds and runs a probe, such as a
  temporary test in the repository's unit-test binary. When the build tree
  does not match the target's base, record a way to build against matching
  sources, such as a temporary branch whose changed files equal the target's,
  and restore the tree after each probe.

### Mode: First, Follow-Up, or Full

Decide the mode, and record it with its reason in `target.md` as `Mode:`:

1. When the user asks for a full review, the mode is `full`.
1. Otherwise, find the earlier run of the same target: the run this session
   already made, or the newest entry under `<archive>/<repo>/<key>/`. With
   none, the mode is `first`.
1. With an earlier run, compute the delta from its reviewed range
   (`<earlier base>..<earlier head>`) to the new one, and save it to
   `delta.patch`:
   - The earlier head is an ancestor of the new head
     (`git merge-base --is-ancestor`) and no merge commit lies between them:
     `git diff <earlier head> <new head>`.
   - Otherwise, for a merge of `main` or a rebase:
     `git range-diff <earlier base>..<earlier head> <new base>..<new head>`.
   - When `range-diff` cannot match the commits, the mode is `full`, and the
     review still runs the fix verification below.
1. The mode is `follow-up`. Both agents follow
   `references/follow-up-review.md`. Copy into `target.md` the earlier run's
   directory and range, the path of `delta.patch`, and every earlier finding
   whose status was `accepted`, `unverified`, `unresolved`, or `dropped`, with
   its current text, status, and probe paths.

Say the mode and its reason to the user when the run starts, so they can ask
for another one.

For a SHA target that is not the current checkout, add a detached worktree
under the run directory (`git worktree add --detach <run>/tree <sha>`) and run
both reviews there, so both agents read full files at the reviewed commit.
Remove the worktree at the end. A local build then reflects the main checkout,
not the worktree; say so in `target.md`.

If the target is missing or ambiguous, ask the user. Do not guess.

## Step 2: Independent Reviews (Round 0)

Start the peer first, in the background when the harness supports it, with the
rendered `peer-review-prompt.md`. Then write your own review.

**Do not read the peer's review until your own review file is written.** The
two reviews must be independent.

Each review has two parts:

1. **Design review:** follow the `system-design-review` skill, then run the
   five checklists in `references/design-review-checklist.md` and put their
   tables in `## Coverage`.
1. **Code review:** when the repository has
   `.agents/skills/review-diff/SKILL.md` (or `review-pr` for a PR target),
   follow that engine but do not post to GitHub. Otherwise, check correctness,
   boundary and degraded paths, error handling, invariants across callers,
   and test coverage of the changed behavior.
1. **Code review checklists:** run the five checklists in
   `references/code-review-checklists.md` (parameter contracts with doc
   comments and diagnostics, branches and tests, assertion quality,
   reachability, structure) whichever engine ran, and put their tables in
   `## Coverage`.

For each new public API, check empty, negative, duplicate, and wrong-typed
arguments; the parameter-contract table records the result.

Give every finding its Reached evidence, and every claim that an input does or
does not reach the code a row in checklist 4. When a probe can be built, build
it: a trigger of yours is `built` before you report it as `Bug`. Build each
probe through the parser, so the validity layers run. Run each probe that may
crash in its own process, and do not change the reviewed tree while the peer
reads it.

Write every finding in the format of `references/finding-format.md`. Claude
uses IDs `CL-1`, `CL-2`, …; Codex uses `CX-1`, `CX-2`, …. Use the section
order the peer prompt asks for, including the two-sentence summary in place of
the Background; the full Background is written once, in the report.

Apply the Fix Check of `system-design-review` to the Next step of every
finding, code findings included.

Check the peer's output before you use it. Rerun the peer once, naming what is
missing, when:

- it does not follow the finding format; or
- in follow-up mode, its `## Fix verification` table lacks a row for an
  earlier finding; or
- its `## Coverage` section is missing, or shows that it skipped the design
  review or the code-review engine without a reason such as a missing skill;
  or
- its `## Coverage` section lacks any of the five design checklist tables or
  the five code checklist results; or
- it reports no design finding and has no `## Design candidates not reported`
  list.

If the rerun fails the same check, stop as for a peer failure.

A peer finding whose Reached is `read` or `not built` is not a format failure;
Step 3 checks it.

## Step 3: Build the Ledger

Write `ledger.md` with one row per finding from both reviews:

| ID | Kind | Current title | Raised by | Reached | Claude | Codex | Status |
| -- | ---- | ------------- | --------- | ------- | ------ | ----- | ------ |

- The raising agent's column starts as `raised`; the other column starts empty.
- **Reach check.** Before round 1, the orchestrator tries to build the trigger
  of every finding whose Reached is not `built` or `hypothetical`, the peer's
  and its own, and records the result below the table: `built` with the probe
  and its result; `rejected by <layer>` with the layer's reason; or
  `cannot build` with why. Update the Reached column from it. A trigger that a
  layer rejects is evidence against the finding; the raising agent answers it
  in round 1.
- Below the table, keep the **current text** of every finding that has been
  revised, copied from the answer file that revised it. Rows without a
  revision use their round-0 text.
- When two findings state the same root cause, keep both rows and let the
  agents mark them `duplicate-of` in round 1. Do not merge them yourself.

The orchestrator updates the ledger only by the rules below. It does not
rewrite either agent's text; it copies it and names the source file.

## Step 4: Exchange Rounds (at most 3)

One round has two ordered steps:

1. The peer answers every open row, using the rendered
   `peer-exchange-prompt.md`.
1. The orchestrator reads the peer's answers, then answers every open row.

The order lets the orchestrator accept a peer revision in the same round. A
revision from the orchestrator reaches the peer in the next round.

| Answer               | Meaning                                                   |
| -------------------- | --------------------------------------------------------- |
| `agree`              | The finding is valid as currently written.                |
| `disagree`           | The finding is wrong; give code, IR, or test evidence.    |
| `revise: <change>`   | Valid after a change to category, Reached, wording, or Next step. |
| `withdraw`           | Only for one's own finding: it is wrong.                  |
| `duplicate-of: <ID>` | Same root cause as another row; keep the clearer one.      |
| `keep`               | Only for one's own finding: no change from its last text. |

An answer that disputes a finding must cite evidence, such as a file and line,
an IR snippet, or a test command and its output. An answer without evidence
counts as `agree`.

Whether an input reaches the code takes the same evidence in both directions,
as checklist 4 sets out. An answer that says an input does not reach the code
names the rejecting layer and gives a probe that this layer rejects; without
both it counts as `agree`. An `agree` with a finding whose Reached is `read` or
`not built` means you checked its layers yourself; say which ones.

Each answer covers the Next step too. If the Next step fails the Fix Check of
`system-design-review`, answer `revise` with a Next step that passes,
and cite the owner or the same-class input as evidence.

After both answers, update each row from its current text:

- **accepted:** the raising agent answers `keep` and the other answers
  `agree`; or one agent's `revise` gets `agree` from the other in the same
  round (peer revision) or the next round (orchestrator revision); or both
  agents give the same `revise`. Use the accepted text.
- **unverified:** a row that meets **accepted**, but whose Reached is below
  what its category needs in `references/finding-format.md`, for example a
  `Bug` that is `read` or `not built`. It needs a probe, not more agreement.
- **dropped:** the raising agent answers `withdraw`, or both agents answer
  `disagree`.
- **merged:** both agents mark the same `duplicate-of` target.
- **open:** anything else. A `disagree` answers the text it was given; when
  the other agent revised the row in the same round, the row stays open and the
  next round answers the revision.

Stop early when no row is open, or when a round changes no status and adds no
revision. After round 3, every open row becomes **unresolved**.

Do not raise new findings in exchange rounds. If an agent finds a new problem
while it checks a disputed claim, it lists it under `Late findings`; these go
to the report without a consensus status.

Either agent may mark a ledger entry `ledger-error` when the ledger misstates
its answer. Fix the entry from that agent's response file before the next
round.

## Step 5: Report

Write `final.md`, then show it to the user in their preferred language:

1. **Target:** the reviewed SHA range, the run directory, and the mode with
   its reason.
1. **Fix verification** (follow-up mode): one line per earlier finding with
   both agents' verdicts. Say whether the review has converged, as
   `references/follow-up-review.md` defines.
1. **Background:** the Background defined in the Output section of
   `system-design-review`, written for the accepted findings.
1. **Consensus findings:** accepted findings, most severe first, design and
   code findings in separate lists. Start each finding with one plain sentence
   that ties it to the background, then use the format in
   `references/finding-format.md`, including its Reached evidence.
1. **Unverified findings:** for each row, the finding, why its trigger is not
   built, and the probe that would settle it.
1. **Unresolved disagreements:** for each row, the finding, the strongest
   argument from each agent with its evidence, and the check that would decide
   it.
1. **Dropped findings:** one line each, with the reason.
1. **Late findings:** listed separately, marked as reviewed by one agent only.
1. **Process:** rounds used, peer reruns or failures, each probe the
   orchestrator built with its result, and coverage gaps from either agent's
   `## Coverage`, such as tests that neither agent could run.

When the user asks for text for the author, use the `review-comment-drafting`
skill with the accepted findings the user picks.

Then archive the run at the path in **Run Directory**: copy `target.md`,
`ledger.md`, `final.md`, every `review-*.md` and `round-*.md`, and the probe
sources from `probes/` (inputs such as `.mlir`, `.cpp`, `.py`, `.sh`, each under
50 KB). Do not copy builds, worktrees, logs, patches, or probe outputs. Give
the archive path in the report.

Do not post anything to GitHub. If the user asks to post, follow
`review-comment-drafting`.
