# Code Review Checklists

Run these three checklists in every code review, in addition to the engine or
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

## Low-Severity Fixes

A finding from these checklists may have no failing input in the current
callers. Report it when the fix is local and cheap, such as an assert, a
stronger assertion, or a sentence in a doc comment. Use the `Maintainability`
or `Nit` category, write the input that would reach it as the Trigger, and
start the Next step with `Optional:`. Do not drop it for lack of a current
caller.
