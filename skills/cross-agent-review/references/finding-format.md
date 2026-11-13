# Finding Format

Every finding in a review uses this block. Keep each field to one or two
sentences, and put long evidence in a fenced block below it.

```markdown
### <ID> [<kind>] <category>: <short title>
- **Location and evidence:** <file:line, IR snippet, or test output>
- **Trigger:** <the concrete input, path, or state that reaches the problem>
- **Impact:** <what breaks, for whom, or which contract it violates>
- **Next step:** <a fix direction that passes the fix check, or the check that settles the question>
```

- `<ID>`: `CL-<n>` for Claude, `CX-<n>` for Codex.
- `<kind>`: `design` or `code`.
- `<category>` for a design finding: `Confirmed defect`, `Design question`, or
  `Optional trade-off`, as defined by `system-design-review`.
- `<category>` for a code finding: `Bug`, `Missing test`, `Maintainability`,
  or `Nit`. Use `Bug` only when a concrete trigger produces wrong behavior.

Report a finding only when its location, trigger, and impact are supported by
evidence. Drop a finding that cannot be shown on the real code or IR.

The Next step of every finding, design or code, must pass the **Fix Check** in
the `system-design-review` skill: reuse the existing owner of each concept the
fix decides, and do not let a same-class input skip an existing check. When it
cannot pass, give the check that settles the question instead of a fix.

When a review has no findings, say so in one line and list only material
verification gaps.
