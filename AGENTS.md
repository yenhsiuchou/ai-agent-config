# Shared Agent Preferences

These preferences apply across projects. A project rule takes precedence when
it is more specific or stricter.

## Design

- Derive designs from first principles: state the core problem and constraints
  before proposing a solution.
- Check each change against the whole design. Do not accept a locally correct
  change that breaks a global invariant or layering boundary.
- Keep the design principles in the `system-design-review` skill's
  `references/design-principles.md`, such as atomic transitions, in every
  design and fix you propose, including review findings. A smaller patch that
  breaks one is not a fix.
- Cover normal, degraded, and boundary paths before proposing a design.
- Treat existing code as a choice that can change, not as a constraint.
  Separate real constraints (hardware, external contracts, stated global
  invariants) from behavior that exists only because earlier code was written
  that way. Design from the real constraints first. For each gap between that
  design and the current code, decide explicitly: fix the code first in a
  prerequisite change, isolate the workaround behind one boundary and record
  it as debt, or keep it with a stated reason. Never work around a flaw
  silently.

## Implementation

- Prioritize correctness. Establish invariants before performance or other
  concerns.
- Reuse an existing abstraction when it fits. Design new abstractions for
  reuse when doing so does not add unnecessary complexity.
- Split large changes into small, self-contained changes that can be reviewed,
  verified, and reverted independently.

## Git Branches

- When you start work on a branch, run `git fetch` first. If local `main` is
  behind `origin/main`, fast-forward it (`git fetch origin main:main`).
- On a branch that is not pushed yet, rebase onto `main` when you need newer
  `main` changes.
- On a branch that is already pushed, fast-forward to `origin/<branch>` first
  (`git merge --ff-only origin/<branch>`), because the remote may hold a
  "Update branch" merge or a teammate's commit. If the fast-forward fails
  because both sides have new commits, stop and ask.
- A pushed branch based on `main`: do not rebase. Merge `main` in if you need
  it, then plain push.
- A pushed stacked branch (based on another PR's branch): when the base branch
  changes or is merged, rebase onto the new base
  (`git rebase --onto <new base> <old base>`; after the base PR is
  squash-merged, the new base is `main`).
- Force-push only after such a stacked rebase, and use
  `git push --force-with-lease --force-if-includes`, so git refuses the push
  when the remote holds commits your branch does not include.

## Clarification

- Before starting work, ask when anything is unclear or ambiguous. Do not make
  assumptions.
- During implementation, ask only when uncertainty materially affects
  requirements, scope, public API, or design trade-offs.
- For small, reversible details, make a reasonable assumption and state it in
  the handoff.
- State design flaws, technical debt, and limits plainly.
- When a conclusion depends on code behavior, finish the trace before you
  report it: name the exact function, its callers, and whether it is on the
  path. Follow the actual calls from the entry point; a name match is not a
  trace. Do not report a half-checked claim with a "not fully confirmed"
  caveat. A review skill that gives a finding an explicit status, such as
  `unverified` with its next probe, keeps that status.

## Language

- Reply in Chinese and English. Keep technical terms, code, and identifiers in
  English; write other explanation in Chinese.
- Write plan-mode plan files and reports for the user in Chinese the same way:
  keep technical terms, code, identifiers, and file paths in English.
- Use simple English with direct words and sentences. Do not use Japanese.

## Content And Code

- Keep explanations to the smallest amount that conveys the point.
- Start explanations with a simple intuition, then introduce technical detail.
- Keep code comments about the code's behavior or design constraint. Put
  reasoning history and before/after discussion in commits or reviews.
- When you link to a file, use a repo-relative path for a file inside the
  current repository and an absolute path for any file outside it. Never use a
  `file://` URI; the user's editor cannot open it.
- When the user asks to design a new feature with them, asks for a top-down
  design, or runs `/top-down-design`, use the `top-down-design` skill. It
  decides one level at a time and calls `cross-agent-design-doc` once at the
  end.
- When the user asks to write a design document (design doc, 設計文件,
  design 文件) in one pass, or to review an existing one, use the
  `cross-agent-design-doc` skill and run its full review.
  Use `reader-first-writing` for a design document only when the user asks for
  an English version for a repository.
- Before writing other text for other readers—PR descriptions, review
  replies, commit messages, code comments, diagnostics, names, or test text—use
  the `reader-first-writing` skill.
- For a PR description, an English design document, a new pass, or a large
  diff, run the `reader-first-writing` cold-reader check when independent
  reviewer tooling is available.
- Before drawing a diagram in a Markdown file, use the `markdown-diagrams`
  skill. A chat reply has no diagram block; use a table or arrow text.

## Personal Skill Ownership

- Treat this repository's `skills/` directory as the sole source of truth for
  the user's reusable skills. Create and update personal or cross-project
  skills here, then install them through this repository's `install.sh`.
- Add a skill to a project's `.agents/skills/` only when the user explicitly
  requests a project-owned shared workflow, or when the skill inherently
  depends on that project's code, tools, contracts, or team process. Do not
  copy a personal skill into a project repository for convenience.
- When ownership is unclear, ask before choosing a skill location.
- After adding or changing a memory, skill, hook, or rule in this file, run
  the `agent-config-review` skill in `changed` mode on the changed files, so
  that no two sources ask for different behavior in the same situation.

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
- When the user asks for a review of a design document by both agents, use
  `cross-agent-design-doc`. A PR or a diff still uses `cross-agent-review`.
- To analyze or address reviewer comments on the user's own PR, use
  `verify-reviewer-comments`.
- To draft or post review comments on another author's PR, use
  `review-comment-drafting`, whichever review produced the findings. It
  replaces the posting step of a project review skill, such as `review-pr`,
  because the comments go out under the user's account.
