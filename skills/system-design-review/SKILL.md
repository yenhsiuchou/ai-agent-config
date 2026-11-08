---
name: system-design-review
description: Review a code change for evidenced system-design problems in problem framing, ownership, architecture boundaries, lifecycle cost, and evolution. Use as a separate lens alongside, not instead of, routine correctness, performance, security, and test review.
---

# System Design Review

Use this skill for a design-focused review of a PR, commit, range, branch, or
working-tree diff. It is useful when a change adds a compiler pass, IR
contract, cross-layer interface, runtime policy, representation change, or
other decision whose effects extend beyond one local implementation.

Do not use it as a substitute for ordinary correctness, performance, security,
or test review. When the request also names `review-diff` or `review-pr`, run
that review independently. Do not invoke it yourself or ask whether to invoke
it. In a combined result, keep only the clearest finding for a shared root
cause; this skill contributes the system-level evidence.

## Establish the Problem

1. Resolve the review target and read its goal, full changed files, and relevant
   tests. Read the source and documentation that define a changed interface or
   pass contract, rather than inferring intent from a diff alone.
1. Record a short ledger:
   - **Facts:** behavior established by code, tests, measurements, or docs.
   - **Assumptions:** claims that depend on an unverified condition.
   - **Unknowns:** information required to judge the design but not available.
1. State the problem, success condition, trigger, and affected users or stages.
   If the evidence does not establish them, retain the uncertainty; do not
   invent design intent.

## Trace Ownership and Costs

For each decision with non-local impact, build an information-and-ownership
timeline:

| Decision | Required information | Information owner | Decision owner | Pipeline position | Stable representation? |
| -------- | -------------------- | ----------------- | -------------- | ----------------- | ---------------------- |
| ...      | ...                  | ...               | ...            | ...               | yes / no / unknown     |

Use the timeline to examine whether a decision runs after its required facts
exist and at the component responsible for its resulting state transition.
`Atomic` means that one component owns one complete semantic transition and the
information needed for it. It does not mean that every feature must use one
pass: preparation and emission may belong at different information boundaries.

Compare alternatives only against the project's actual goal and usage. Include
runtime, compile-time, memory, maintenance, test, debugging, coupling, and
foreclosed-option costs that the available evidence supports. A more specialized
implementation is valid when its evidence and ownership are clear.

## Audit Terminology and Semantic Contracts

When a diff changes the scope, implementation, documentation, or use of a
named concept, predicate, attribute, flag, or pass classification, trace that
concept before accepting the local change. This includes a predicate that starts
recognizing more operations, derived values, representations, or pipeline
stages than before.

Build a semantic-contract ledger for the changed term:

| Name | Definition at this stage | Producer | Consumers | Persisted representation or invariant | Evidence |
| ---- | ------------------------ | -------- | --------- | ------------------------------------- | -------- |
| ...  | ...                      | ...      | ...       | ...                                   | ...      |

Search the term, its implementation predicate, its annotations or flags, its
verifiers, and its documentation. For a compiler, also trace direct producer
and consumer passes. Do not infer that two uses share a definition merely
because they use the same name.

For this audit, **output ownership** means that a loop selects the machine
element responsible for producing an output value. A **machine-coordinate
classification** only establishes that a loop participates in addressing a
machine element; it does not imply output ownership or parallel execution. A
**representation boundary** makes a distinction enforceable when a distinct
IR type, attribute, operation, or verified pass contract carries it.

When the ledger shows different scopes, decide which of these is intended:

1. one definition is being deliberately widened for every consumer;
1. the contexts describe different concepts and need distinct names; or
1. a representation boundary makes a context-specific meaning unambiguous.

The third case is valid only when a consumer can inspect the distinction in an
IR contract: a type, attribute, operation, or verifier. A comment that calls
both meanings phase-specific is not enough.
If the evidence does not establish the choice, report a **Design question**.
State the conflicting definitions, a concrete input that reaches the broader
case, which consumers would interpret it differently, and the smallest next
step: define the term globally, introduce a narrower name or predicate, or
document and enforce a representation boundary.

Do not require a new persistent annotation merely because a local pass needs a
derived classification. Prefer a named local predicate when the property is
cheaply derivable and has no cross-pass semantic contract.

## Report Only Actionable Design Work

Report a candidate only when the review can establish all of these:

- a location and evidence;
- a concrete trigger;
- a meaningful impact on a user, contract, stage, cost, or failure mode; and
- a minimum next step: a focused change or a verification that resolves the
  uncertainty.

Use these categories:

- **Confirmed defect:** evidence establishes a violated contract or a real,
  reproducible harmful behavior.
- **Design question:** a material decision cannot be judged because key intent
  or evidence is missing.
- **Optional trade-off:** a concrete alternative has different costs, and the
  project goal decides between them.

Do not report a future concern merely because another implementation might
arrive someday. Do not call a design insufficiently general without a supported
trigger and causal impact. If no item meets the bar, say so plainly and list
only material verification gaps.

When an existing component demonstrably owns the required information and state
transition, give a concrete alternative: name what remains where it is, what
moves to the owner, which cross-stage dependency disappears, and how to verify
the result. Do not fabricate a replacement architecture when the owner or
contract is unknown.

## Output

Start with a two- or three-sentence model of the change and its evidence limits.
Then use this structure for every reported item:

```markdown
### <category>: <short title>
- **Location and evidence:** ...
- **Trigger:** ...
- **Impact:** ...
- **Next step:** ...
```

For Sonic-mlir compiler changes, read
`skills/system-design-review/references/sonic-mlir-middle-end.md` when
the diff touches a pipeline, IR contract, collective communication, NoC,
resource mapping, or backend lowering. Read only the sections selected by the
changed boundary. In particular, read its semantic-contract navigation when a
diff changes a loop classification, machine-coordinate predicate, or spatial
flag. For calibrated examples and maintenance rules, read
`skills/system-design-review/references/calibrated-cases.md`.
