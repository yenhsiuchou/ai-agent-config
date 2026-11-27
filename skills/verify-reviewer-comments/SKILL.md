---
name: verify-reviewer-comments
description: Analyze the review comments on the user's own PR with evidence for each verdict, then apply the fixes the user approves and draft the replies. Use when the user asks to look at, analyze, triage, or address reviewer comments or review feedback on their own PR, such as "看一下 reviewer 的意見".
---

# Verify Reviewer Comments

A reviewer comment is a claim about the code. Each verdict you give the user,
whether accept, adjust, or decline, must rest on evidence you checked, not on a
function name, a doc sentence, or a probe that failed for another reason.

This skill covers comments on the user's own PR. For comments on another
author's PR, use `review-comment-drafting`.

## Step 1: Collect

1. Fetch every review and inline comment, with its path, line, commit, and node
   ID. Note a comment made on an outdated commit, and check whether the current
   code still has the problem.
1. Align the local branch with the remote before reading code. For a stacked PR,
   note which branch introduced the code each comment touches.

## Step 2: Classify

Give each comment one kind:

| Kind | Example | Evidence it needs |
| ---- | ------- | ----------------- |
| Reachability or correctness | "this input writes the wrong elements" | Step 3 |
| Missing test | "this branch has no test" | a test, plus a mutation that it catches |
| Design or structure | "move this state out of the context" | the owner of the concept, the callers it changes, and Step 5 |
| Naming, comment, or message | "this name is vague" | the project rules for names and comments |

## Step 3: Check Reachability and Correctness

When a comment says an input reaches wrong behavior, or when your answer will
say an input cannot reach the code, fill this table:

| Claim | Rejected by (file:line on the live path) | Probe | Reject reason seen | Verdict |
| ----- | ---------------------------------------- | ----- | ------------------ | ------- |

- **Rejected by:** follow the call path from the code under review to the line
  that rejects the input, and read each function on it in full. A helper with a
  fitting name that the path does not call is not evidence.
- **Probe:** build an input that passes the rule's weak points, such as
  `front()`, the first match, an early `break`, a check of one side only, or a
  check of each dim alone without the relations between dims. Do not stop at
  variants of the reviewer's example.
- **Reject reason seen:** the failure message or debug log of the probe. A probe
  rejected by a different rule is not evidence for the cited rule.
- **Verdict:** `unreachable` needs both columns filled. Otherwise the input is
  reachable: handle it with a failure reason and a test, not an assert.

When the reviewer writes that they have not built a failing case, try to build
one before you answer. Before you tell the user a case is unreachable, give the
code and the claim, not your conclusion, to an independent agent, such as
`codex:rescue`, and ask it to build a counterexample.

For a project, read its review context for the analysis it relies on: the
`README.md` in `~/.agent-config-local/review-context/<repository directory name>/`,
when it exists, says which file and section apply to the code a comment
touches.

## Step 4: Check Missing Tests

For each test the comment asks for, or that your fix adds:

1. Write the test and run it.
1. Break the code it covers, for example by removing the check or replacing a
   value with a constant, and confirm that the test fails. Restore the code.
1. If the case cannot be built, give the rule that blocks it, with Step 3
   evidence.

## Step 5: Check Each Change Against the Design Principles

A reviewer's suggestion can fix the problem it names and still break a design
principle. For each change a comment asks for, and for each change you plan,
fill the Principle Gate of
`../system-design-review/references/design-principles.md`, plus the project
principles in the review context.

- A suggestion that breaks a principle gets the verdict `adjust`, with a change
  that fixes the same problem and keeps every principle, or `decline`, with
  the principle's question and its answer as evidence.
- Give each planned change to a fresh agent with
  `../system-design-review/references/principle-gate-prompt.md`, without your
  reasoning. Change a plan the gate marks `breaks` before you report it.

## Step 6: Report Before Changing Code

Show the user one table, one row per comment:

| # | Location | Claim | Evidence | Verdict | Planned change | Principle gate |
| - | -------- | ----- | -------- | ------- | -------------- | -------------- |

- Evidence is a file:line, a probe with its result, or a mutation result.
- Principle gate is `pass`, or the principle the reviewer's suggestion breaks
  and how the planned change keeps it.
- Say plainly when your verdict differs from the reviewer's suggestion, and why.
- Wait for the user's decision. Do not change code in this step.

## Step 7: Apply and Reply

After the user approves:

1. Change the code on the branch that owns it. Merge it up the stack with a
   signed-off merge.
1. Run the tests that cover the change, and the mutations from Step 4.
1. Run a code review of the change and apply its real findings, then commit
   and push without asking the user, following the project's commit and PR
   rules. The user already approved which comments to fix in Step 6; ask
   again only when a fix would change the design.
1. Update the PR description so that it still matches the diff.
1. Draft the replies with `reader-first-writing`. Each reply states what
   changed, or the evidence for not changing it, in one or two sentences. A
   reply for an unreachable case names the rule that rejects it. Do not mention
   commits.
1. Post the replies as a pending review, following the project's PR rules, so
   the user submits them.
