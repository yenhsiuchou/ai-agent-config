# Shared Agent Preferences

These preferences apply across projects. A project rule takes precedence when
it is more specific or stricter.

## Design

- Derive designs from first principles: state the core problem and constraints
  before proposing a solution.
- Check each change against the whole design. Do not accept a locally correct
  change that breaks a global invariant or layering boundary.
- Cover normal, degraded, and boundary paths before proposing a design.

## Implementation

- Prioritize correctness. Establish invariants before performance or other
  concerns.
- Reuse an existing abstraction when it fits. Design new abstractions for
  reuse when doing so does not add unnecessary complexity.
- Split large changes into small, self-contained changes that can be reviewed,
  verified, and reverted independently.

## Clarification

- Before starting work, ask when anything is unclear or ambiguous. Do not make
  assumptions.
- During implementation, ask only when uncertainty materially affects
  requirements, scope, public API, or design trade-offs.
- For small, reversible details, make a reasonable assumption and state it in
  the handoff.
- State design flaws, technical debt, and limits plainly.

## Language

- Reply in Chinese and English. Keep technical terms, code, and identifiers in
  English; write other explanation in Chinese.
- Use simple English with direct words and sentences. Do not use Japanese.

## Content And Code

- Keep explanations to the smallest amount that conveys the point.
- Start explanations with a simple intuition, then introduce technical detail.
- Keep code comments about the code's behavior or design constraint. Put
  reasoning history and before/after discussion in commits or reviews.
- Before writing text for other readers—PR descriptions, design documents,
  review replies, commit messages, code comments, diagnostics, names, or test
  text—use the `reader-first-writing` skill.
- For a PR description, design document, new pass, or large diff, run the
  `reader-first-writing` cold-reader check when independent reviewer tooling is
  available.
