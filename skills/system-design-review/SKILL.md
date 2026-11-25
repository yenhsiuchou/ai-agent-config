---
name: system-design-review
description: Perform an evidenced design or architecture review of a PR, diff, code change, or design document. Use when the user says design review, even with a PR number; do not replace it with routine review-pr unless that review is also explicitly requested.
---

# System Design Review

Use this skill when the user asks for a design review or architecture review of
a PR, commit, range, branch, or working-tree diff, or of a design document
(see **Target: A Design Document**). A PR number or URL names
the target; it does not request routine `review-pr`. This skill is useful when
a change adds a compiler pass, IR
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
1. Read the design documents in the repository that the change or its stack
   builds on, before judging its intent.
1. When a change applies a transformation in more cases than its description
   motivates, find the check that makes the transformation necessary before
   you question its scope. Trace the failing precondition to the IR contract
   it enforces. If the transformation restores that contract, the contract
   defines its scope, not the description's motivation.
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
`references/design-principles.md` states this rule and the other principles
that every design and every fix must keep.

Before you report that a decision ignores a cost, find the component that owns
that cost: a pass in the pipeline, a PR in the same stack, or an open PR by the
same author. When another component owns it, judge each component against its
own objective. Do not ask the upstream component to also optimize the
downstream cost; that merges two decisions that the ownership timeline keeps
apart. Report only a cost that the change leaves without an owner, or an
interim state the author does not acknowledge.

Report the reverse case. When one component optimizes objectives whose
information or decision belongs to different owners, give the owner table and
propose splitting the decision at that boundary.

Compare alternatives only against the project's actual goal and usage. Include
runtime, compile-time, memory, maintenance, test, debugging, coupling, and
foreclosed-option costs that the available evidence supports. A more specialized
implementation is valid when its evidence and ownership are clear.

## Question Necessity

A review that only checks whether the change does what it says will never ask
whether it needs to. For each element the change adds — a second path such as a
fast path, special case, or fallback; a validation or failure path; a new
concept, field, or flag — fill one row:

| New element | What needs it (caller or input source, file:line) | Owner of the guarantee it checks or adds | What breaks without it | Verdict |
| ----------- | ------------------------------------------------- | ---------------------------------------- | ---------------------- | ------- |

- **Read from the source.** Trace each caller from where its input is created
  to the call, including later PRs of the same stack. The lines around the
  call are not enough: a rebuild or a normalization earlier in the caller can
  already guarantee what the new element checks.
- **Empty "what breaks".** When the column holds no concrete input, the element
  re-checks a guarantee an upstream owner already holds, or serves an input no
  caller produces. Report a **Design question** with the caller trace, and offer
  the smaller alternative: reuse the owner, state a precondition with an
  assert, or remove the element.
- **Validate at the boundary, assume inside it.** A function whose input comes
  from IR or from other components reports a failure on bad input. A helper
  whose input comes only from the owner of an invariant asserts that invariant.
  Decide which one a function is from its producers, not from a policy comment
  the change itself writes; the change's own design rules are claims to check,
  not evidence.
- **A second path for performance.** Ask for a measurement at the stage where
  the cost is paid, and check whether the inputs it receives differ from those
  of the main path. When it gives the same output as the main path on every
  input a caller produces, its only value is speed; say so with the numbers.
- **Cost of asking.** A necessity question is cheapest on a design document or
  the first PR of a stack. Late in a stack, raise one that removes code; one
  that adds code needs stronger evidence.

## Separate Real Constraints From Incidental Code

A change often bends its design around how existing code happens to work.
Each bend is a design decision. When nobody states it, the next change treats
the workaround as a constraint too, and the flaw spreads.

List every place where the change shapes itself around existing code: an
adapter, a conversion, a special case, a flag, a second representation, or a
reason such as "because pass X currently does Y". Fill one row for each:

| Bend | Existing behavior it follows (file:line) | Real or incidental | Decision the change states | Verdict |
| ---- | ---------------------------------------- | ------------------ | -------------------------- | ------- |

- **Real constraint:** hardware, an external contract (another repository, a
  simulator, a file format), or a global invariant the project states. The
  design must keep it.
- **Incidental:** behavior that exists only because earlier code was written
  that way. Show that it could change: its owner is in this repository, and
  no real constraint requires it.
- Each incidental bend needs one explicit decision: fix the existing code
  first, in a prerequisite change; isolate the workaround behind one boundary
  and record it as debt; or keep it with a stated reason.
- **Silent bend:** an incidental bend with no stated decision. Report a
  **Design question**. Give the design without the bend, the prerequisite
  change that removes it, and that change's size. When the prerequisite is
  large, isolating the bend is an accepted answer: the finding is about the
  silence, not a demand to fix the old code now.
- **Leaking bend:** a workaround the change says it isolates, but that new
  logic outside the boundary also depends on. Report a **Design question**
  that names each place it reaches.

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
case, which consumers would interpret it differently, and the next
step: define the term globally, introduce a narrower name or predicate, or
document and enforce a representation boundary.

Do not require a new persistent annotation merely because a local pass needs a
derived classification. Prefer a named local predicate when the property is
cheaply derivable and has no cross-pass semantic contract.

## Check the Design Principles

Fill the Principle Gate of `references/design-principles.md` for the change
itself, and for each project principle in the review context. A break with a
built trigger is a **Confirmed defect**; a break whose trigger is not built is
a **Design question**.

## Report Only Actionable Design Work

Report a candidate only when the review can establish all of these:

- a location and evidence;
- a concrete trigger;
- a meaningful impact on a user, contract, stage, cost, or failure mode; and
- a next step: a change that passes the fix check below, or a verification
  that resolves the uncertainty. Choose the fix that keeps the design
  principles, not the smallest patch; a local patch often breaks them.

Measure a cost at the stage where it is paid. An op count after an early pass
is not a runtime or compile-time cost; lower the IR to where the cost
materializes, or do not claim the cost.

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

## Fix Check

A proposed fix applies the ownership rule above to the fix itself. Apply this
check to the Next step of every finding, including a code finding from another
review engine:

- **Owner:** for each concept the fix decides (which ops read a value, what an
  output is, which check rejects a case), name its existing definition: a
  helper, interface, verifier, or pass. Reuse it or move the decision there.
  Do not define the concept a second time in the changed code.
- **Same class:** list the inputs that the fix classifies differently from the
  current code, including variants of the trigger (for example, the same read
  that is also written). Check each against the existing checks and tests on
  that path. The fix must not let one of them skip a check.
- **Principles:** fill the Principle Gate of
  `references/design-principles.md` for the fix. A fix that breaks a
  principle is not a fix: replace it with one that keeps every principle,
  even when it is larger, and give its size.
- Prefer a fix that removes a special case over one that adds a rule.

When a fix cannot pass this check, give the check or the decision that
settles the question instead of a fix.

**Independent gate.** Before the output, give the Next step of every finding
to a fresh agent with `references/principle-gate-prompt.md`, as the
Independent Gate in `references/design-principles.md` says. When the harness
cannot start an agent, say so in the evidence limits.

## Target: A Design Document

A design document proposes a change that does not exist yet. Review it with
the same rules, read against the current code instead of a diff:

- **Facts against code.** Record each factual claim of the document in the
  Facts ledger: what a pass does today, which inputs reach a path, what an IR
  example shows. Find its evidence: a file:line, a test, or IR from a command
  you ran. A claim the code contradicts is a `Confirmed defect`; a claim with
  no evidence is an Assumption, and a design decision that rests on it is a
  `Design question`.
- **Necessity.** Fill the necessity table for every pass, concept, field,
  check, or fallback the document adds. Read each caller from where its input
  is created in the current code. This is the cheapest time to ask.
- **Constraints.** Check that the document designs from real constraints
  first, and that its list of gaps with the current code covers every
  incidental bend, each with one decision (see **Separate Real Constraints
  From Incidental Code**).
- **Ownership.** Build the ownership timeline for each proposed decision:
  does it run after its facts exist, at the component that owns the result?
- **Paths.** Check that the document covers the normal, degraded, and
  boundary paths, and says what happens on each: an error, a fallback, or a
  skip, consistent with other handlers of the same input class.
- **Alternatives.** Compare the proposal with the alternatives that the
  project goal and the existing owners support, including the smaller one:
  reuse an owner, or do nothing.
- **Change split.** When the document splits the work into PRs or steps,
  check that each one can be reviewed, verified, and reverted alone, and that
  no step leaves the pipeline in a state the document does not acknowledge.
- **Terms and figures.** Each term is defined once and used with one meaning.
  Each diagram and IR example agrees with the text next to it.
- **Principles.** Fill the Principle Gate for the document's proposal, one
  table per decision that changes the IR.

The Fix Check applies to the document's own proposal as it does to a finding's
Next step. Report findings in the format the calling skill gives; without one,
use the Output section below, with the document section and a quote as the
location.

## Output

Start with a **Background** that explains the change to a reader who has not
read the PR, so the findings make sense on their own. Write it from the code
and the PR text, and mark any intent the evidence does not establish.

- **Problem:** one sentence of intuition, then a real, trimmed IR or code
  snippet (from the PR's tests or a probe) that shows what goes wrong without
  the change.
- **Approach:** what the change does to that snippet, or the rule it adds, in a
  few sentences. Name new functions only where a finding refers to them.
- **Terms:** define once each term that the findings use and the reader may not
  know, such as a pass-specific concept. For a tensor or machine concept, use
  an index expression, not prose.
- **Where the findings hit:** one line per finding that points at the part of
  the problem or approach it questions.
- **Evidence limits:** what the review could not check.

Keep the background to what the findings need, about one screen. Start each
finding with one plain sentence that ties it to the background, such as "In
the dispatch example above, the routing step also reads the table." Then use
this structure for every reported item:

```markdown
### <category>: <short title>
- **Location and evidence:** ...
- **Trigger:** ...
- **Impact:** ...
- **Next step:** ...
- **Principle gate:** pass | waived by the user: <principle, reason>
```

Put the Principle Gate tables in a `## Principles` section after the findings,
with the result of the independent gate for each finding.

A project may have local, non-versioned review context at
`~/.agent-config-local/review-context/<repository directory name>/`. When it
exists, read its `README.md`, which says which file covers which kind of
change, and read only the sections selected by the changed boundary. If this
local context is absent, do not infer project-specific architecture from this
skill; state that the review needs the live project contracts and has that
evidence limit.
