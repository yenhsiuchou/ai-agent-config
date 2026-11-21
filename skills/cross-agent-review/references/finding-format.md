# Finding Format

Every finding in a review uses this block. Keep each field to one or two
sentences, and put long evidence in a fenced block below it.

```markdown
### <ID> [<kind>] <category>: <short title>
- **Location and evidence:** <file:line, IR snippet, or test output>
- **Trigger:** <the concrete input, path, or state that reaches the problem>
- **Reached:** built | read | not built | hypothetical — <the evidence, below>
- **Impact:** <what breaks, for whom, or which contract it violates>
- **Next step:** <a fix direction that passes the fix check, or the check that settles the question>
```

- `<ID>`: `CL-<n>` for Claude, `CX-<n>` for Codex.
- `<kind>`: `design` or `code`.
- `<category>` for a design finding: `Confirmed defect`, `Design question`, or
  `Optional trade-off`, as defined by `system-design-review`.
- `<category>` for a code finding: `Bug`, `Missing test`, `Maintainability`,
  or `Nit`.

## Reached

The Trigger is a claim that an input exists and reaches the code. **Reached**
says how that claim was shown. An input reaches the code only if it passes every
validity layer in front of it, listed in checklist 4 of
`code-review-checklists.md`.

| Value | Meaning | Evidence to give |
| ----- | ------- | ---------------- |
| `built` | The input was built, passed the parser and every validity layer, and reached the code | the probe command and its result |
| `read` | The path was traced in the code, and each validity layer on it was read and accepts the input | each layer with its file:line |
| `not built` | Neither of the above, for example because the reviewer runs read-only | why it was not built |
| `hypothetical` | No current caller passes the input; the finding concerns a contract a future caller could break | the caller or contract that would pass it |

A layer that the reviewer did not read does not count as accepting the input.
An input that a layer rejects does not reach the code, and the finding is
wrong: a fix for it adds dead code.

## Category and Reached

| Category | Allowed Reached |
| -------- | --------------- |
| `Bug`, `Confirmed defect` | `built` |
| `Missing test` | `built` or `read` |
| `Maintainability`, `Nit`, `Design question`, `Optional trade-off` | any |

A finding whose Reached is `not built` keeps its category until the
orchestrator checks it (SKILL.md, Step 3).

A suspected design problem whose trigger you could not build is a
`Design question` with Reached `not built`. It needs a location, the suspected
trigger, and the caller trace that leads to it; its Next step is the probe that
settles it. Report it rather than drop it for lack of a probe: the orchestrator
builds the probe before round 1.

A finding whose Reached is
`hypothetical` starts its Next step with `Optional:`. Report such a finding
when the fix is local and cheap, such as an assert of a caller precondition, a
stronger assertion, or a sentence in a doc comment; do not drop it only because
no current caller reaches it.

## Fix Check

The Next step of every finding, design or code, must pass the **Fix Check** in
the `system-design-review` skill: reuse the existing owner of each concept the
fix decides, and do not let a same-class input skip an existing check. When it
cannot pass, give the check that settles the question instead of a fix. A fix
that adds a check must name an input that reaches it; a check that no input
can reach is dead code.

When a review has no findings, say so in one line and list only material
verification gaps.
