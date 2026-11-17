# Code Review Checklists

Run these five checklists in every code review, in addition to the engine or
the general checks. Put each table in the review's `## Coverage` section, even
when it has no gap. A row with a gap becomes a finding, or a reason why not.

Checklist 4 decides whether an input reaches the code. The other checklists
use it whenever a row depends on such an input.

## 1. Parameter Contracts

One row per parameter of each new or changed public API, and per field of a
struct it reads.

| API | Parameter | Assumed by the code | Enforced by | Gap |
| --- | --------- | ------------------- | ----------- | --- |

- **Assumed by the code:** every property the body relies on, such as length,
  order, distinct values, a range, or agreement with another argument.
- **Enforced by:** an assert, a reported failure, a type, or one of the
  validity layers in checklist 4, with its file:line. Write `none` when
  nothing enforces it.
- A caller that does not exist yet does not close the gap. When a wrong value
  writes out of bounds, overwrites data, or produces wrong IR silently, report
  it with Reached `hypothetical`, normally as `Maintainability` with an assert
  of the precondition as the Next step.

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
- **One clause per diagnostic:** a failure reason names one condition, and
  each distinct cause has its own reason. A phrase that joins three
  conditions, such as "a loop without constant bounds inside the machine dim
  and step 1", becomes one condition or a list. A reason that names the wrong
  cause, such as "a loop that is not unit-step" for an index that is not a loop
  at all, is a hit.
- **Unchecked guarantee:** a comment that says some input never occurs, such
  as "which an all-gather never does", needs a row in checklist 4. Without one,
  the guarantee is a hit.

Report each hit as `Maintainability` or `Nit`.

## 2. Branches and Tests

One row per branch in the changed code: each `if`/`else`, early `return`,
`continue`, `switch` case, and failure path.

| Location | Condition | Test that reaches it | Assertion that fails if the branch is wrong |
| -------- | --------- | -------------------- | ------------------------------------------ |

- Write `none` when no test reaches the branch, or when no assertion would
  fail on a wrong result. A `none` is a `Missing test` when an input reaches the
  branch (Reached `built` or `read`). When you think no input can reach it, add
  a checklist 4 row; an unreachable branch is dead code, not a missing test.
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
  message. Report the mismatch, and ask for a test of each side that an input
  reaches.
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
  for example a check for presence where the value matters. A mutation of the
  code under test, such as removing a check or fixing a value, shows whether
  the assertion fails.

Report each hit as `Missing test` or `Maintainability`.

## 4. Reachability

Whether an input reaches the code decides whether a finding is real, whether a
branch needs a test, and whether a check is dead code. The answer takes the
same evidence in both directions.

### Validity Layers

An input reaches the code only if it passes every layer in front of it:

1. **The parser**, including custom assembly formats.
1. **The verifier of the op itself**, including its traits and interfaces.
1. **The verifier of every enclosing op.** A region op often checks the
   accesses in its body; for example, a region op's verifier may reject an
   out-of-bound memory access that the `memref.load` verifier accepts.
1. **Verification between passes**, which the pass manager runs on the whole
   module.
1. **The analyses the caller runs first**, such as building a normalized view,
   and the preconditions the caller must hold.

To find a layer, trace the live path from where the input is created to the
code, and read each function on it in full. A helper with a fitting name that
the path does not call is not a layer. Note the layers that only look at part
of the input: `front()`, the first match, an early `break`, a check of one side
only, or a check of each dim alone without the relations between dims.

### Claims

One row per claim that an input reaches, or does not reach, the code. Claims
come from findings, from the code or its comments, from the author's
description, from your own reasoning, and from the two sources below.

| Claim | Direction | Layers on the path (file:line) | Probe and its result | Verdict |
| ----- | --------- | ------------------------------ | -------------------- | ------- |

- **Reaches:** the probe passes every layer and reaches the code. Without a
  probe, list each layer you read and why it accepts the input; that is
  Reached `read`, not `built`.
- **Does not reach:** name the layer that rejects the input, and give a probe
  that this layer rejects, with its reason. A probe rejected by a different
  layer is not evidence for the named one. Build the probe to pass the weak
  points of the other layers.
- **Verdict:** `reaches`, `does not reach`, or `open` when the evidence of
  neither direction is complete. Treat `open` as reaching for a missing check:
  a failure reason with a test, not an assert. An assert on an input that
  reaches is a `Bug`, because a debug build crashes and a release build
  produces wrong output.

### Sources of Claims

**Dropped relations.** A rewrite that rebuilds output from parts of its input,
such as one loop per dim, one value per slot, or one op per element, keeps only
the relations it copies. Any relation between those parts that it does not
copy is dropped: a value shared by two dims, an equality between bounds, or an
order between ops. Each dropped relation is a claim: either a layer rejects
inputs that have it, or the rewrite produces wrong output for them.

**Mixed coordinate spaces.** Code that reads one representation with an index
that belongs to another, for example result `dim` of an original access map
while `dim` and the shapes beside it come from a normalized view. The two
agree only under an invariant some layer enforces; that is a claim. When one
representation can serve both reads, report the mix as `Maintainability` and
suggest reading from that one.

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
ordering dependency gives wrong behavior on an input that reaches it.
