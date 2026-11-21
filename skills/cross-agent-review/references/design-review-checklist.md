# Design Review Checklists

Run these five checklists in every design review, after the ownership timeline
and the necessity table of `system-design-review`. Each one searches for a
shape of design problem that a read of the diff alone does not show: you find
it by running the pipeline, searching the code, or measuring. Put each table
in `## Coverage`, even when it has no gap. A row with a gap becomes a finding,
or a reason why not.

A reviewer who cannot build a probe, such as a read-only peer, runs the built
tools on existing test files or on IR passed on stdin, which writes no file.
A check that needs a new file or a rebuild becomes a suspected trigger: report
it as the finding format says for an unbuilt `Design question`, and the
orchestrator builds it.

## 1. Stated Invariants Against Pipeline IR

One row per property the change relies on about its input: a sentence in the
PR description, a doc comment, or a design document, or an assert in the
changed code. For example, "such a loop pushes or pops only the queues of its
own PE".

| Invariant | Stated in | IR checked (command) | Counterexample | Verdict |
| --------- | --------- | -------------------- | -------------- | ------- |

- Look for a counterexample in the IR that the real pipeline gives the code,
  not only in the PR's own tests. Run the upstream passes on existing test
  inputs of the same area, and read their output at the changed pass.
- A counterexample that passes every validity layer (checklist 4 of
  `code-review-checklists.md`) is a `Confirmed defect`. When it passes but
  gives no wrong result today, the rule holds only under an unstated
  condition: report a `Design question` that names the condition.

## 2. Policy Consistency

One row per outcome the change decides for an input class: an error, a
warning, a fallback, a skip, or a silent pass.

| Outcome | Input class | This change does | Other handler of the same class (file:line) | It does | Verdict |
| ------- | ----------- | ---------------- | ------------------------------------------- | ------- | ------- |

- Find the other components that handle the same input class or the same
  outcome: a verifier, an earlier or later pass, an option such as
  `fail-on-...`, or a sibling path in the same pass.
- A different policy for the same class with no stated reason is a
  `Design question`. For example, one pass makes an unfolded pad an error
  while another pass only warns on a host round trip; or task formation fails
  hard where the verifier only warns.

## 3. Existing Owners

One row per concept, analysis, or helper the change adds.

| New concept | Search (command) | Existing owner (file:line) | Same definition? | Verdict |
| ----------- | ---------------- | -------------------------- | ---------------- | ------- |

- Search the code for a component that already computes the same fact: the
  names, the predicates, the attributes it reads, and the passes that produce
  them. Record the search command even when it finds nothing.
- A second definition feeds the ownership timeline and the Fix Check of
  `system-design-review`. For example, a second analysis of "content is the
  same on every PE", or bound parsing in a tool beside the shared bound
  helpers.

## 4. Limits and Fast Paths, Measured

One row per cap, limit, threshold, budget, or second path for speed.

| Element | Claimed effect | Measurement (command, input, numbers) | Verdict |
| ------- | -------------- | ------------------------------------- | ------- |

- Measure at the stage where the cost is paid, with an input near the limit.
  For example, a 40-variable cap on a solver call: time one call at 21, 33,
  and 39 variables.
- A cap that does not bound the cost it names is a `Confirmed defect`. A fast
  path gives speed only; report its numbers as an `Optional trade-off` against
  the second implementation it adds.
- Without a measurement, write `not measured` and do not claim the cost.

## 5. Scope of New Checks

One row per new rejection, guard, or classification in the change.

| New check | Motivating input | Other input classes it now treats differently | Probe at base and at head | Verdict |
| --------- | ---------------- | --------------------------------------------- | ------------------------- | ------- |

- List the inputs that the check treats differently from the base beyond the
  motivating case, and probe one input of each class that the base accepted.
  For example, a guard added for a non-linear index that asserted may also
  reject a single-term non-linear index that worked.
- A class that worked at the base and now fails, with no stated reason, is a
  `Design question`. The Fix Check of `system-design-review` applies the same
  test to a proposed fix; this row applies it to the change itself.

## Candidates Not Reported

Under `## Design candidates not reported`, list every design candidate that
you considered but did not report, one line each, with the reason: the owner holds the guarantee (file:line), a layer
rejects the trigger, or no trigger was found after a named search. A design
review that reports no finding and lists no candidate is incomplete.
