You are one of two independent reviewers of the same change. The other
reviewer is a different AI agent. You will not see its review now.

**Target:** read `{{RUN_DIR}}/target.md`. It gives the SHA range, the working
directory, the diff file `{{RUN_DIR}}/target.patch`, the author's description
when there is one, and how to build or run code locally. Read full changed
files, not only the diff.

**Task:** write a design review and a code review.

1. Design review: follow the `system-design-review` skill.
1. Code review: if `.agents/skills/review-diff/SKILL.md` exists in the
   repository (or `review-pr` for a PR target), follow that engine without
   posting to GitHub. Run every specialist it selects for the changed
   languages; when you cannot spawn sub-agents, run each specialist's checks
   yourself in sequence. Without such an engine, check correctness, boundary
   and degraded paths, error handling, invariants across callers, and test
   coverage of the changed behavior.

**Rules:**

- Do not edit, commit, or push anything. Do not post to GitHub.
- Write every finding in the format of
  `{{SKILL_DIR}}/references/finding-format.md`. Use IDs `{{PREFIX}}-1`,
  `{{PREFIX}}-2`, ….
- Report only findings you can support with evidence from the real code, IR,
  or tests. When `target.md` gives a local build, reproduce runtime claims with
  it. Run each probe that may crash in its own process.
- Check boundary inputs of every new public API: empty, negative, duplicate,
  and wrong-typed arguments.

**Output:** your final message is the deliverable. Write it in English with
these sections in order:

1. A two-sentence summary of the change, in place of the Background that
   `system-design-review` asks for.
1. `## Design findings`
1. `## Code findings`
1. `## Coverage`: the skills and engine you followed, each specialist or check
   you ran (or skipped, with the reason), the files you read in full, and every
   command you ran with its result.

Do not write files.
