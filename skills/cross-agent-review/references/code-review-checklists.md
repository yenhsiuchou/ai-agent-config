# Code Review Checklists

Run these four checklists in every code review, in addition to the engine or
the general checks. Put each table in the review's `## Coverage` section, even
when it has no gap. A row with a gap becomes a finding, or a reason why not.

## 1. Parameter Contracts

One row per parameter of each new or changed public API, and per field of a
struct it reads.

| API | Parameter | Assumed by the code | Enforced by | Gap |
| --- | --------- | ------------------- | ----------- | --- |

- **Assumed by the code:** every property the body relies on, such as length,
  order, distinct values, a range, or agreement with another argument.
- **Enforced by:** an assert, a reported failure, a type, or a verifier that
  runs before the call. Write `none` when nothing enforces it.
- A caller that does not exist yet does not close the gap. When a wrong value
  writes out of bounds, overwrites data, or produces wrong IR silently, report
  it, normally as `Maintainability` with an assert or a check as the Next step.

Also check that the doc comment states each assumption a caller must hold, and
what the API does to each output parameter on success and on failure.

## 2. Branches and Tests

One row per branch in the changed code: each `if`/`else`, early `return`,
`continue`, `switch` case, and failure path.

| Location | Condition | Test that reaches it | Assertion that fails if the branch is wrong |
| -------- | --------- | -------------------- | ------------------------------------------ |

- Write `none` when no test reaches the branch, or when no assertion would
  fail on a wrong result. Report each `none` that a valid input can reach as
  `Missing test`; check a verifier before calling a branch unreachable.
- Short branches count. A branch of one line that removes an attribute or
  returns early needs a row like any other.

## 3. Assertion Quality

For each new or changed test assertion, check:

- **Printer-dependent text:** it matches SSA names (`%2`, `%arg3`), attribute
  order, or other printer output that can change without a behavior change.
  Prefer checking the structure: an op, its map, its result count, or its type.
- **Partial match:** it matches only a prefix or a fixed part of a message
  whose rest is built by the code under review, so the built part is untested.
  Check the built part too.
- **Weak oracle:** it would still pass if the behavior it names were wrong,
  for example a check for presence where the value matters.

Report each hit as `Missing test` or `Maintainability`.

## 4. Dropped Relations and Upstream Guarantees

A rewrite that rebuilds output from parts of its input, such as one loop per
dim, one value per slot, or one op per element, keeps only the relations it
copies. Any relation between those parts that it does not copy is dropped:
a value shared by two dims, an equality between bounds, or an order between
ops.

| Rewrite | Input relation not copied | Rejected by (file:line on the live path) | Probe and its reject reason | Gap |
| ------- | ------------------------- | ---------------------------------------- | --------------------------- | --- |

Use the same table for every claim that an upstream analysis, verifier, or
caller rejects an input, whether the claim is in the code, the author's
description, or your own reasoning.

- **Rejected by:** the line that runs on this path, read in full. A helper with
  a fitting name that the path does not call is not evidence.
- **Probe:** an input built to pass that rule's weak points: `front()`, the
  first match, an early `break`, a check of one side only, or a check of each
  dim alone without the relations between dims. Record the reason the probe was
  rejected. A probe rejected by a different rule is not evidence for this one.
- **Gap:** without both columns filled, treat the input as reachable. Report a
  missing check as `Bug` when a probe reaches wrong output, else as
  `Missing test` or `Maintainability`. An assert on such an input is a `Bug`
  finding, because a debug build crashes and a release build produces wrong
  output.

## Low-Severity Fixes

A finding from these checklists may have no failing input in the current
callers. Report it when the fix is local and cheap, such as an assert of a
caller precondition, a stronger assertion, or a sentence in a doc comment. Use the `Maintainability`
or `Nit` category, write the input that would reach it as the Trigger, and
start the Next step with `Optional:`. Do not drop it for lack of a current
caller.
