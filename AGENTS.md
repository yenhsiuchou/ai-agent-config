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

## Personal Skill Ownership

- Treat this repository's `skills/` directory as the sole source of truth for
  the user's reusable skills. Create and update personal or cross-project
  skills here, then install them through this repository's `install.sh`.
- Add a skill to a project's `.agents/skills/` only when the user explicitly
  requests a project-owned shared workflow, or when the skill inherently
  depends on that project's code, tools, contracts, or team process. Do not
  copy a personal skill into a project repository for convenience.
- When ownership is unclear, ask before choosing a skill location.

## Review Skill Selection

- When the user asks for a design review or architecture review, use
  `system-design-review`, including when the target is a PR number or URL. A PR
  target alone does not select `review-pr`.
- Use `review-pr` or `review-diff` only when the user asks for code review,
  correctness review, a full review, or explicitly names one of those skills.
  When the user explicitly requests both review types, run both and keep their
  findings distinct until duplicate root causes are merged.
- When the user asks for a review by both Claude and Codex, or for a
  cross-agent or consensus review, use `cross-agent-review`. It runs both the
  design review and the code review in each agent.
