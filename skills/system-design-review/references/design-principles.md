# Design Principles

These principles hold for every design a review judges or proposes: the change
under review, the proposal of a design document, the Next step of each finding,
and the change a reviewer comment asks for. A review that finds a break reports
it. A review never proposes a fix that breaks one.

Each principle has a question. Answer it for the design in front of you; a
`yes` is a break.

## The Principles

### atomic-transition

One component owns one complete semantic transition and the information it
needs. When the component finishes, the IR is in a state that a type, an op,
or a verifier defines, and no later component has to finish the transition.
Preparation and emission may still belong to different components when each
one ends in such a state.

**Question:** After this design runs, can the IR be in a state between two
components that no verifier recognizes, or that a later component must
remember to complete?

Common breaks:

- Change part of the IR in one pass and leave the rest to a later pass
  ("widen here, fix the users later").
- Split one rewrite into steps across components, where each step alone
  produces IR that no contract defines.
- Add a downstream patch that completes a transition an upstream component
  started.

### decide-equals-apply

The code that decides whether a transformation applies is the code that
performs it, or both read one plan. A transformation either completes or
leaves its input unchanged.

**Question:** Can the check say yes and the rewrite then fail or do something
different? Can the code fail after it has already changed the IR?

Common breaks:

- A `can...` predicate kept beside the rewrite, with its own copy of the
  rewrite's conditions.
- A failure path, such as `return failure()` or an early `break`, after the
  first mutation.
- A fix that adds a condition to the check but not to the rewrite, or to the
  rewrite but not to the check.

### no-side-channel

Each guarantee a consumer relies on lives in a type, an op, a verifier, or a
written contract of the component that produces it.

**Question:** Does correctness depend on an attribute, a marker, a naming
convention, or a pass order that nothing verifies, so that a component that
drops or ignores it produces wrong output with no error?

Common breaks:

- A marker attribute that a later pass must read and every pass between them
  must keep.
- A comment that states a precondition that no assert or verifier checks.

### single-owner

Each concept, fact, or predicate has one definition, at its owner.

**Question:** Does the design define again a fact that an existing helper,
analysis, interface, verifier, or pass already computes?

Common breaks:

- A local predicate beside a shared helper that answers the same question.
- A second analysis of a property that another pass already establishes and
  records.

### guarantee-at-source

A component whose input comes from IR or from other components checks that
input and reports a failure. A helper whose input comes only from the owner of
an invariant assumes that invariant and asserts it.

**Question:** Does the design add a guard downstream for a guarantee that an
upstream owner should hold, or move a check away from where the input is
created?

Common breaks:

- A defensive check in a consumer for a case that the producer should never
  create; fix the producer, or assert.
- A fallback that hides a broken upstream guarantee.

### decision-at-owner

A decision runs after the facts it needs exist, at the component that owns its
result. A component optimizes only its own objective.

**Question:** Does the design make a component decide before its facts exist,
reach back to change an earlier decision, or optimize a cost that another
component owns?

Common breaks:

- An upstream pass that also tunes a downstream cost.
- A late pass that rewrites a choice an earlier pass made, instead of moving
  the choice to the late pass.

### one-policy-per-class

Each class of input gets one outcome, an error, a warning, a fallback, or a
skip, across every component that handles it, unless the design states why it
differs.

**Question:** Does the design give an input class a different outcome than
another handler of the same class, with no stated reason?

### no-silent-bend

When a design follows behavior that exists only because earlier code was
written that way, it states one decision: fix that code first, isolate the
workaround behind one boundary and record it as debt, or keep it with a
reason.

**Question:** Does the design shape itself around incidental existing behavior
without stating that decision?

## Project Principles

A project may add its own principles in its review context
(`~/.agent-config-local/review-context/<repository directory name>/`). Use
them with the same question format; the gate checks them too.

## Principle Gate

Fill this table for each design you judge or propose: the change, the
document's proposal, and the Next step of every finding.

| Principle | Verdict | Evidence |
| --------- | ------- | -------- |
| atomic-transition | keeps / breaks / n/a | ... |
| ... | ... | ... |

- **Evidence** names the code or text that settles the question: the
  component that ends the transition, the plan that the check and the rewrite
  share, the verifier that holds the guarantee, or the owner that the fix
  reuses. `n/a` needs one clause on why the principle does not apply.
- A Next step that breaks a principle is not a fix. Replace it with a design
  that keeps every principle, even when that design is larger than a local
  patch; give its size. When you know no such design, report a
  `Design question` that names the principles in conflict and the decision or
  check that settles it.
- Only the user waives a principle, for one named finding. Record the waiver
  and its reason in the finding. A reviewer never writes a waiver.

## Independent Gate

The reviewer who wrote a fix tends to accept it. When the harness can start a
new agent, give each Next step to a fresh agent with
`principle-gate-prompt.md`. Give it the principles, the finding, and the code
location; do not give it the reviewer's reasoning. A finding whose Next step
the gate marks `breaks` is rewritten until the gate passes it, or becomes a
`Design question` as the Principle Gate says. Record each gate result in the
report.
