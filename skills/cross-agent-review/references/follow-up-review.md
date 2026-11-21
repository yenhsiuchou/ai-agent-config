# Follow-Up Review

A follow-up review checks a target that an earlier run already reviewed, after
the author changed it. It answers two questions: did the changes fix the
earlier findings, and did they add a new problem? It does not review the
unchanged code again for small issues; the earlier run already did.

`target.md` gives what this review needs: `Mode: follow-up`, the earlier run's
directory and range, the delta file `delta.patch`, and the earlier findings
with their current text and probes.

## Part 1: Fix Verification

One row per earlier finding whose status was `accepted`, `unverified`, or
`unresolved`:

| Earlier ID | Earlier Next step | Change in the delta (file:line) | Probe at the new head (command, result) | Verdict |
| ---------- | ----------------- | ------------------------------- | --------------------------------------- | ------- |

- Rerun the earlier probe on the new head when one exists. A probe that needs
  a rebuild is the orchestrator's; a reviewer that cannot rebuild writes
  `not rerun` and reads the change instead.
- **Verdict:** `fixed`, `not fixed`, `fixed with a new problem`, or
  `no longer applies` (the code it named is gone).
- A verdict other than `fixed` or `no longer applies` is also a finding, in
  the finding format, titled `Not fixed: <earlier ID> …` or
  `New problem in the fix of <earlier ID>: …`. It keeps the earlier category
  unless the evidence changes it.
- Do not raise again an earlier finding whose status was `dropped`, unless the
  delta removes the reason it was dropped. Say which line does.

## Part 2: Delta Review

Run the design review, the code review, and both sets of checklists on the
delta only: the lines it changes, and the callers and callees whose behavior
those lines change. Fixes often add new code, comments, tests, and doc text;
these get the full checklists.

## Part 3: Unchanged Code

In code that the delta does not change, report only a `Bug` or a
`Confirmed defect`. Do not report a `Missing test`, `Maintainability`, `Nit`,
`Design question`, or `Optional trade-off` there; the earlier run already had
the chance to raise it.

## Output

Put `## Fix verification`, with the table above, before the other sections of
the review.

## When To Stop

When a follow-up run accepts no finding above `Nit`, the review has converged.
The report says so and does not recommend another run.
