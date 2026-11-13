---
name: reader-first-writing
description: >-
  Write and edit technical text from the reader's starting point, then perform
  a cold-reader check. Use for PR descriptions, design docs, review replies,
  commit messages, code comments, diagnostics, names, and test text; not for
  ordinary conversational answers.
---

# Reader-First Writing

A text is readable when it begins with what its reader knows, uses names they
can find in the code, and makes its behavior concrete.

## Know The Reader

Identify the intended reader and provide what they do not know:

| Text | Reader already knows | Supply |
|---|---|---|
| PR description | Project pipeline | This change and why it is needed |
| Design doc | Project pipeline | The model and its terms |
| Review reply | Their own comment | What changed and why |
| Commit message | Repository | This specific change |
| Code comment | Nearby code | The constraint behind it |

When reader and purpose are unclear, infer them from the artifact. Ask only
when a wrong choice would materially change the text.

## General Rules

1. **Lead with the point.** State what was missing or wrong and what now works
   in the first two lines.
2. **Use code names.** Name a pass, operation, type, or function exactly as it
   appears in code. Define an unavoidable new term once at first use.
3. **One idea per sentence.** Prefer sentences of about 25 words or fewer.
4. **Use label headings.** Prefer `Problem`, `Change`, `Example`, `Tests`, and
   `Stack` over headings that make claims.
5. **Show changed behavior.** Include a trimmed before/after example of ten
   lines or fewer, then say what to notice.
6. **Say what it is.** Start with the positive statement; do not define a
   subject only by what it is not.
7. **Match size to the change.** Small diffs need short descriptions. Put
   details after the main point.

## By Artifact

- **PR description:** `Problem` (2–3 sentences), `Change` (one bullet per
  behavior change), `Example` when behavior changes, `Tests`, then `Stack`.
  Follow project-specific PR rules when present.
- **Design doc:** Begin with the problem and a real code or IR example, then
  present the model. Define each term once in a short `Terms` table.
- **Review reply:** State what changed in the code or doc, or why no change is
  made. Add at most a short reason. Do not cite a commit or hash; the reviewer
  reads the current diff.
- **Commit message:** The subject says what the change does in code names. Add
  a body only when the reason is not obvious.

## Code Text

Comments, diagnostics, identifiers, and test text follow the same rules. In
addition:

1. **Comments name the condition, then its reason.** State the checked
   condition in code form, then name the source: an op definition, type
   constraint, or caller invariant.
2. **Index properties show a tiny map.** For an access map or index property,
   prefer an example such as `(d0) -> (d0 * 4 + d1)` over prose alone.
3. **Use operational verbs.** Prefer `maps`, `returns`, `is constant`, and
   `equals` over personifying verbs.
4. **Name referenced code.** Name the actual pass or function.
5. **Diagnostics state expected versus actual.** Keep them to one clause with
   values. Put a reason in the preceding comment when needed.
6. **Identifiers use code and domain nouns.** Do not introduce metaphor nouns
   unless the domain already defines them.
7. **Keep test text short.** A test comment documents one behavior in one line;
   the function name states the case.

For a new pass or file, and for changed code exceeding about 300 lines, apply
the cold-reader check to file headers, doc comments, comments, and diagnostics,
not function bodies.

## Cold-Reader Check

Apply this check to every PR description and design document. Skip it for
commit messages and review replies. Apply it to code in the cases above.

An independent cold reader must have no authoring context. Give them only:

- a PR description and its final diff;
- a design document alone; or
- for code, only changed file headers, doc comments, comments, and diagnostics.

Ask them:

> You know the repository's domain but not this change. Read the text below
> (and the diff when provided).
>
> 1. In two sentences, say what problem it solves and what it changes.
> 2. List every word or phrase whose meaning you had to guess.
> 3. Name the sentence that was hardest to read.
>
> Do not suggest rewrites.

For code, replace question 1 with: "In two sentences, say what this component
does. For each diagnostic, say in one line what input it rejects."

Compare the report with the intended change:

- Rewrite text when the summary is wrong or vague.
- Use the code name, define, or remove every guessed term.
- Split the hardest sentence.

Run at most one more independent check after rewriting. If anything remains
unclear, report it instead of looping.

When independent reviewer tooling is unavailable, perform the same questions as
a self-check. Do not call it independent. Do not expose documents or code to an
external reviewer without authorization.
