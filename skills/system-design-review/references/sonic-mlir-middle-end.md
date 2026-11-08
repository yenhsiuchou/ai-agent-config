# Sonic-mlir Middle-end Design Model

Use this reference for Sonic-mlir compiler changes. It is a navigation and
reasoning model, not a replacement for the live pipeline and contracts. Confirm
every current-state claim against the source named below before reporting it.

## Global Map

| Stage                  | Responsibility                                               | Source of truth                                                                               |
| ---------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| Torch-MLIR ingress     | Introduce SonicCompute IR from Torch-MLIR                    | `sonic-mlir/lib/torch-mlir/Pipelines.cpp`                                                     |
| SonicCompute lowering  | Transform and normalize graph-level and loop-based IR        | `sonic-mlir/lib/Dialect/SonicCompute/Pipelines/SonicComputePipelines.cpp`                     |
| Communication and NoC  | Select collective form, create NoC legs, route and map them  | the SonicCompute pipeline plus the communication passes it registers                          |
| SonicMachine contracts | Define machine-level operations and resource representations | `sonic-mlir/doc/Dialect/SonicMachine/Specification.md` and its pass docs                      |
| Backend lowering       | Verify normal form and lower device functions toward LLVM    | `sonic-mlir/lib/Conversion/Pipelines.cpp` and `sonic-mlir/doc/Designs/Lowering/NormalForm.md` |

Read the pipeline builder first when a diff changes pass order. Then read the
changed pass, its direct producer and consumer, the applicable dialect contract,
and a test that shows the intended transition. `MappingPasses.md` is the entry
point for resource-mapping ownership and the exclusive-level invariant.

## Semantic-Contract Navigation

Machine-coordinate and loop-classification changes can look local while
changing the meaning of a term used across multiple stages. When a diff changes
`spatial`, a machine-dimension predicate, a loop flag, or a loop-reordering
classification, trace the live source of each role before judging it:

Here, a **machine element** is one physical hardware coordinate. A
**machine-dimension predicate** asks whether loop-derived addresses include
such a coordinate. `#sonic.spatial` is a persisted IR flag; determine its
meaning from its producer and verifier rather than from its name.

| Role                 | Source navigation                                                       | Question to answer                                                                                   |
| -------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Local classification | changed pass and `LoopUtils` / `IRUtils` helpers                        | Which memory operations and derived IVs make a loop qualify?                                         |
| Persisted meaning    | `AnnotateSpatialLoopFlags`, `DistributeUtils::annotateSpatialLoopFlags` | Which operations define a `#sonic.spatial` flag, and which machine element owns the produced output? |
| Enforced invariant   | `VerifyBackendLowering`                                                 | Which definition does backend verification require?                                                  |
| Communication use    | `UnrollSpatialLoopsForCommunication`, `InsertNocBuffers`                | Does communication need source, destination, routing-table, or FIFO-coordinate loops instead?        |

Do not treat an input-side machine-coordinate access as output ownership merely
because both are described as spatial. Output ownership means selecting the
machine element that produces an output; machine-coordinate classification only
means that a loop participates in addressing a machine element. Conversely, do
not assume a loop that is unflagged is irrelevant to communication
normalization. If the changed pass needs the broader property, determine
whether it is a deliberate global redefinition of `spatial` or a separate
machine-coordinate classification. The answer must be reflected in naming,
flags, verification, and documentation; if the change does not establish it,
report a design question rather than silently accepting phase-specific
terminology.

## Communication and NoC Model

This model begins at a collective `sonic.move`. Trace earlier construction only
when a changed contract depends on it.

| Boundary                                       | Current or planned status                                                    | Owner and decision                                                                                                   | Review contract                                                                                                                                                                                         |
| ---------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SplitMultiLevelMoveOps`                       | Current pipeline                                                             | Split a collective crossing multiple machine levels into per-level moves                                             | Preserve intermediate buffer indexing, payload, alias behavior, and synchronization semantics. Check whether the next pass still receives the representation it requires.                               |
| Communication library replacement              | Planned design; verify the phase in `CommunicationLibraryMoveReplacement.md` | Replace a whole collective before splitting, or in a later planned phase replace a single-level move after splitting | Treat template selection, normalized views, type lifting, recurrent marks, and downstream legality as explicit contracts. Do not assume a planned replacement point exists in the current pipeline.     |
| `LowerAllGatherMoveOps` and broadcast lowering | Current pipeline                                                             | Choose and materialize a delivery algorithm, such as a recurrent ring or read-once/write-many broadcast              | Storage-only changes must not freeze or duplicate algorithm selection. Check that a selected algorithm preserves its data and dependence semantics.                                                     |
| `InsertNocBuffers`                             | Current pipeline                                                             | Turn selected SRAM communication into SRAM-to-NoC, NoC-to-NoC, and NoC-to-SRAM legs                                  | Decisions needing final NoC-leg structure, mapped DMA properties, or final alias-backed access belong here or in its direct helpers. The pass owns move, broadcast, and dynamic communication matchers. |
| Routing, resource mapping, and allocation      | Current pipeline                                                             | Turn NoC legs into routes, mapped resources, and concrete buffers                                                    | Earlier passes must leave machine coordinates, dependences, alignment, and memory-kind information in a form these consumers can read.                                                                  |

### Current Pipeline Questions

For a changed communication feature, trace these questions through the live
pipeline rather than assuming a fixed order:

1. Is the feature deciding collective algorithm, physical storage preparation,
   NoC transfer shape, routing, or resource placement?
1. At which pass do the inputs required for that decision first coexist?
1. Which pass already creates the representation that carries the decision's
   result?
1. Does the proposal require a pass to predict or reconstruct a later
   direct, broadcast, or recurrent representation?
1. Which verifier, test, or downstream pass detects a lost index, alias,
   dependence, alignment, or machine-coordinate contract?

Separate early storage preparation from late transfer emission when their
required information differs. For example, capacity or packing may need to
exist before aliasing, while packet width must wait for final NoC legs and MDES
properties. This is a boundary-specific conclusion, not a rule that all
communication transformations use the same placement.

## Current, Planned, and Open Statements

- A pipeline builder, pass implementation, verifier, or enabled test supports a
  **current fact**.
- A design document supports a **planned design** only when it says the phase is
  not implemented. Use it to review consistency with the proposal, not to claim
  the current compiler behaves that way.
- A documented limitation or unanswered design question is an **open decision**.
  Do not use it as a defect unless the changed code claims to resolve it and
  contradicts its own contract.

When a new case changes this model, update the smallest affected entry with its
source evidence. Keep current facts, rationales, and open decisions separate.
