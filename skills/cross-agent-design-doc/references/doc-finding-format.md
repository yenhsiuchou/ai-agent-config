# Document Finding Format

Every finding uses this block. Keep each field to one or two sentences, and
put long evidence in a fenced block below it.

```markdown
### <ID> <category>: <short title>
- **Location:** <document section> — "<short quote>"
- **Evidence:** <file:line, IR snippet, or command and its output>
- **Reached:** built | read | not built | hypothetical | n/a — <the evidence>
- **Impact:** <what goes wrong if the document stays as written>
- **Next step:** <the edit to the document, or the check that settles the question>
- **Changes decision:** <the decision or section it changes> | no — edge case
- **Principle gate:** pass | waived by the user: <principle, reason>
```

**Changes decision** says whether the finding changes what the document
decides: an ownership, a contract, a mechanism, a PR split, or a stated
constraint. A finding is `no — edge case` when the design stays as written
and only one more input must be handled or tested; its Next step is a row in
the edge-case test list of `驗證`, with the PR that tests it. When several
edge cases come from one design gap, report one finding that names the gap
and the decision it changes, as `extend-by-contract` in
`../system-design-review/references/design-principles.md` says. `Clarity`
findings are `no`.

- `<ID>`: `CL-<n>` for Claude, `CX-<n>` for Codex.
- `<category>`:

| Category | Meaning | Allowed Reached |
| -------- | ------- | --------------- |
| `Confirmed defect` | The code contradicts a claim of the document, or the design breaks an existing contract | `built` or `read` |
| `Design question` | A decision rests on an assumption or misses evidence; the necessity, ownership, or path checks of `system-design-review` raise it | any |
| `Optional trade-off` | A concrete alternative has different costs; the project goal decides | any |
| `Clarity` | The reader would misread the text, a term changes meaning, a diagram disagrees with the text, or a section breaks `doc-style.md` | `n/a` |

**Reached** says how a claim about code behavior was shown, as defined in
`../cross-agent-review/references/finding-format.md`: `built` means a probe
ran through every validity layer; `read` means each layer on the path was read
at a file:line. A suspected problem you could not build is a
`Design question` with Reached `not built` and the probe that settles it in
its Next step.

**Next step** passes the Fix Check of `system-design-review`: it reuses the
existing owner of each concept it decides, lets no same-class input skip an
existing check, and keeps every principle in
`../system-design-review/references/design-principles.md`. Choose the design that keeps the principles, not the smallest edit. For `Clarity`, give the replacement text or the diagram
change.

When a review has no findings, say so in one line and list only material
verification gaps.
