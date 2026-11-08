# Calibrated Cases

These cases calibrate the reporting threshold. They are not universal design
rules. Re-check their cited source when using them as evidence.

## Do Not Report a Hypothetical Future Producer

Commit `f07fed9b28` makes `sonic.device_function` the selector for backend
input. The marker, outlining pass, backend verifier, conversion legality,
pipeline, and tests agree on that contract. A concern that an unspecified future
producer might set or omit the marker has no present trigger or contradiction.
Do not report it merely as an extensibility concern.

## NoC Packetization Has an Ownership Boundary

PR #4568 proposed early packet-layout preparation and a later packet-width
vectorization pass. Its draft placed vectorization before broadcast lowering and
`InsertNocBuffers`, while requiring it to decide from NoC-leg properties,
mapped DMA widths, alias-backed access, and recurrent-ring structure.

The current SonicCompute pipeline creates broadcast form and invokes
`InsertNocBuffers` later. `InsertNocBuffers` owns the move and broadcast
matchers, reads the machine description, and creates the three NoC legs. The
early vectorization placement therefore requires a pass to predict or recreate
several later representations. The concrete risk is a silent scalar fallback or
duplicated algorithm-specific logic when direct communication, broadcast, ring,
or alias behavior differs.

The supported alternative retains early capacity and packing preparation where
aliasing still exposes the necessary storage semantics. It moves packet-width
eligibility and payload strip-mining into `InsertNocBuffers` or its direct
helpers, where final legs and MDES information coexist. Structural tests should
check the selected `vector<N>` push/pop widths and reject an unintended
`vector<1>` fallback.

This case does not mean all transformations belong in `InsertNocBuffers`. It
shows how to identify a decision whose required information and resulting state
transition already have an existing owner.

## Forward Test Candidate

Use commit `e3fe056d1a` as an uncalibrated forward test. Review it from its diff,
contracts, and tests without importing conclusions from these cases. A useful
result may contain no finding. Check that every reported item has evidence, a
present trigger, a concrete impact, and a bounded next step.

## Semantic Scope Must Not Hide Behind One Name

PR #4349 broadened the predicate used by
`ReorderSpatialLoopsOutermost`: a loop can qualify when it indexes a machine
dimension through any kernel memory operation, including an `sml.index_read`
or a derived IV. The established `#sonic.spatial` annotation and backend
normal-form checks instead derive spatial ownership from output memory
operations. Communication lowering also has a source-and-destination endpoint
classification.

The review must not accept these as interchangeable meanings of `spatial`
without tracing their producers and consumers. The present trigger is a dynamic
communication candidate loop that indexes a source or routing-table machine
dimension without directly owning an output machine coordinate. The concrete
risk is that a later pass treats a communication enumeration as an output-owner
parallel loop, or fails to normalize a communication coordinate because it has
no output-owner flag.

This is a **Design question**, not an established miscompile. The bounded next
step is to choose and document one of: a global wider definition of `spatial`
with corresponding annotation and verifier changes; a separately named
machine-coordinate classification for reorder and communication; or an IR
boundary that makes the two meanings unambiguous. Do not select one merely from
this case; compare the affected verifier and resource-ownership contracts.

## Updating This Reference

Add a case only after a user or maintainer has confirmed the judgement. State
the evidence, the decision boundary, and why the item was reported or dropped.
Update a current fact when its source changes; record an unresolved question as
an open decision instead of promoting it to a rule.
