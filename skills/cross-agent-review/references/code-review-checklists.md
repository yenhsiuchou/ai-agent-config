# Code Review Checklists

Run these five checklists in every code review, in addition to the engine or
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

### Doc Comments and Diagnostics

For each new or changed doc comment of a public API, and each new or changed
diagnostic or failure reason, apply the Code Text rules of the
`reader-first-writing` skill, and check:

- **Contract:** the comment states each assumption a caller must hold, as in
  the table above, and what the API does to each output or in-out parameter on
  success and on failure. In-out state includes a builder's or rewriter's
  insertion point.
- **One failure per item:** when an API has two or more failure conditions,
  the comment lists each one as its own item, not one sentence joined by
  commas or `or`.
- **New terms:** a term that the change introduces, such as a field, a
  category of dims, or a role of a buffer, is defined at its first use in the
  comment.
- **Example:** a comment on an index map, a type change, or a layout gives a
  small concrete example, such as `memref<2x2x1xf32>` →
  `memref<2x2x3x4xi32>` or `(d0, d1) -> (d0 * 4 + d1)`.
- **One clause per diagnostic:** a failure reason names one condition. A
  phrase that joins three conditions, such as "a loop without constant bounds
  inside the machine dim and step 1", becomes one condition or a list.

Report each hit as `Maintainability` or `Nit`.

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
- **Helper branches per call site:** when a helper has a branch, such as one
  per loop kind or per operand kind, add one row per call site of the helper.
  A test that reaches the branch from one call site does not cover another. For
  example, a branch that builds an `scf.for` may be reached around a template's
  ring, but not around the outer loops that wrap the template.
- **Symmetric pairs:** when the code handles two sides that play the same role,
  such as input and output, load and store, or lhs and rhs, write one row per
  side and per combination the code can see: both match, only the first,
  only the second. A condition that tests one side alone, as in
  `if (isa<Constant>(outputExpr))`, gives the mirror case a different path or
  message. Report the mismatch, and ask for a test of each side.
- **Promised behavior:** a comment or doc sentence that says what the code
  guarantees, such as "only the machines the matched move runs on take part",
  gets a row of its own with the test that checks it. A promise without a test
  is a `Missing test`, even when no branch belongs to it.

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

Also add a row for each **mixed coordinate space**: code that reads one
representation with an index that belongs to another. For example, it reads
result `dim` of an original access map, while `dim` and the shapes beside it
come from a normalized view. The rows are equal only under an invariant that
someone else enforces; name that invariant and its enforcing line. When one
representation can serve both reads, report the mix as `Maintainability` and
suggest reading from that one.

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

## 5. Structure

Check the changed code for these shapes. Give each hit a location; a shape
without a location is not a finding.

| Shape | Look for | Next step |
| ----- | -------- | --------- |
| Per-call state in a shared context | a field of a context or a struct that one function writes for each call and another function reads, so the reader must call them in order | return the per-call values from the writer, and pass them to the reader; keep the context const after setup |
| Sentinel with two meanings | a null value, `0`, or `-1` that means both a real value and "not set", or a case told apart by a null check at several uses | a named predicate, such as `isIndexedByLoop()`, or a `std::optional` |
| Near-duplicate blocks | two blocks in one function, or in sibling functions, that differ only in which list they read or which value they write | one helper with the difference as a parameter |
| Long positional initializer | an aggregate initialized by position with about five or more fields, or `{}` entries a reader must count | default member initializers, so the call names only the fields it sets |
| Vague helper name | a vague verb with a vague noun, such as `setReason` or `handleData`, or a name that hides that the helper returns `failure()` | a name that says what it does and returns, such as `failOnMachineDim` |
| Mutation that bypasses a tracker | a function that takes an object that records IR or state changes, such as `RewriterBase` or a listener, but changes state without it: `Operation::moveBefore`, `Block::getOperations().splice`, `setOperand`, or `erase` | the tracker's own call, such as `rewriter.moveOpBefore` or `rewriter.modifyOpInPlace` |

Report each hit as `Maintainability`, or as `Bug` when the bypass or the
ordering dependency gives wrong behavior on a concrete input.

## Low-Severity Fixes

A finding from these checklists may have no failing input in the current
callers. Report it when the fix is local and cheap, such as an assert of a
caller precondition, a stronger assertion, or a sentence in a doc comment. Use
the `Maintainability` or `Nit` category, write the input that would reach it as the Trigger, and
start the Next step with `Optional:`. Do not drop it for lack of a current
caller.
