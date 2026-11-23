You are one of two reviewers reading a design document after its review
findings were applied. The other reviewer is a different AI agent; you will
not see its answer now.

**Read:**

- `{{RUN_DIR}}/target.md` for the problem and the repository.
- `{{RUN_DIR}}/doc-r1.md`, the revised document.
- `{{RUN_DIR}}/doc-r0.md`, the document before the review.
- `{{RUN_DIR}}/ledger.md`: each row's status, its accepted text, and the
  section the author edited for it.

**Task:**

1. **Fix verification.** For every row the ledger marks as applied, check the
   edited section against the accepted text. Verdict: `landed`, `wrong` (the
   edit changes something else or says it incorrectly), or `missing`.
1. **Cold read.** Answer as a reader who knows the repository's domain but not
   this design:
   1. In two sentences, what problem does the document solve and what does it
      change?
   1. List every word or phrase whose meaning you had to guess.
   1. Name the sentence that was hardest to read.
1. **Wording.** List small text fixes: a term used with two meanings, a
   sentence to split, a diagram caption that disagrees with its diagram, a
   breach of `{{SKILL_DIR}}/references/doc-style.md`. Give each fix as
   replacement text.
1. **Substantive problems.** Report a design problem only when the revision
   introduced it or the review missed it, with evidence from the code, in
   `{{SKILL_DIR}}/references/doc-finding-format.md` with IDs `{{PREFIX}}-F1`,
   `{{PREFIX}}-F2`, …. Do not re-raise a dropped or unresolved row.

**Rules:** do not edit, commit, or push anything. Do not write files.

**Output:** your final message is the deliverable, in English:

1. `## Fix verification`: | ID | Section | Verdict | Note |
1. `## Cold read`: the three answers.
1. `## Wording`: | Section | Current text | Replacement |
1. `## Substantive problems`: findings, or `None.`
