You are one of two independent reviewers of the same design document. The
other reviewer is a different AI agent. You will not see its review now, and
you did not write the document.

**Target:** read `{{RUN_DIR}}/target.md`. It gives the problem, the
constraints, the success condition, the repository, and how to run the built
tools. The document is `{{RUN_DIR}}/doc-r0.md`. When `target.md` lists an
earlier ledger, read it: raise a finding dropped there again only with new
evidence.

**Task:** design-review the document.

1. Follow the `system-design-review` skill, section **Target: A Design
   Document**, with its ledger, ownership timeline, necessity table, and Fix
   Check. Check every factual claim against the current code in the
   repository, not against the document's own words.
1. Check the document against `{{SKILL_DIR}}/references/doc-style.md`, using
   its self-check table. A row that fails is a `Clarity` finding.

**Rules:**

- Do not edit, commit, or push anything. Do not write files.
- Write every finding in `{{SKILL_DIR}}/references/doc-finding-format.md`.
  Use IDs `{{PREFIX}}-1`, `{{PREFIX}}-2`, ….
- Report only findings that evidence from the real code, IR, or tests
  supports. You may run the built tools in `target.md` on existing test files
  or on IR passed on stdin; a probe run that way is `built`.
- Report a suspected problem you could not build as a `Design question` with
  Reached `not built`; do not drop it for lack of a probe.
- Do not report a preference that the project goal does not support.

**Output:** your final message is the deliverable. Write it in English with
these sections in order:

1. A two-sentence summary of what the document proposes.
1. `## Findings`, most severe first.
1. `## Candidates not reported`: each problem you considered and why it did
   not meet the bar.
1. `## Coverage`:
   - `### Facts`: one row per factual claim of the document:
     | Claim (section) | Evidence (file:line, test, or command) | Verdict |
   - `### Necessity`: the necessity table of `system-design-review`.
   - `### Ownership`: the ownership timeline.
   - `### Style`: the self-check table of `doc-style.md` with pass or fail.
   - The files you read in full and every command you ran with its result.
