# Document Style

The reader is the user: they know the project and want to understand and
decide the design quickly. Write in Chinese; keep technical terms, code, and
identifiers in English.

## More Diagrams, Less Text

- Each section opens with a diagram, a table, or a real IR snippet. Below it,
  at most two or three sentences say what to look at.
- Draw every diagram with the `markdown-diagrams` skill: its formats, colors,
  and DOT check.
- In `設計`, each mechanism (a rule, a flow, an ownership split, a data
  layout) has a diagram. A table supports a diagram there; it does not
  replace one.
- A paragraph longer than three sentences becomes a table, a list, or a
  diagram.
- A table cell holds one clause, about 40 Chinese characters. A cell that
  needs more becomes more rows, a list below the table, or a diagram. Prose
  moved into a cell is still prose.
- Shorter is clearer. When a fix adds text, remove the text it makes
  redundant.

## Recap First

Open with `## Recap：<the concepts recapped>`. Recap every concept the design
builds on that the reader needs, including the current behavior of each
mechanism the design changes. For each concept:

- what it is, in one sentence;
- its rule or mechanism in one small code, IR, or formula block;
- one case it handles or rejects.

For a tensor, layout, or machine concept, use an index expression and a table
of dim → expression → meaning, not prose. Do not add a sentence that announces
the recap.

## Content Rules

- **Conclusion first.** The first line states the problem and the proposed
  answer in one sentence each.
- **Real IR.** Trim examples from tests or probes, and give the command that
  produced them.
- **Evidence in place.** A factual claim names its file:line, test, or
  command.
- **Say what it is.** Start with the positive statement, not with what the
  subject is not.
- **Terms table.** Define each term once in `## 名詞` and use it with one
  meaning.
- **Positions, not history.** Describe the current code and the proposed
  design. Old attempts and review history go to `## Review 紀錄`.

## Self-Check

Run before every review step:

| Check | Pass when |
| ----- | --------- |
| Conclusion | The first two lines state the problem and the answer |
| Recap | Every concept that `問題` and `設計` use without explaining is in the recap or the terms table |
| Diagrams | Every section of `問題` has a diagram, table, or IR block; every mechanism in `設計` has a diagram; every diagram follows `markdown-diagrams` and passes its DOT check |
| Prose | No paragraph exceeds three sentences |
| Cells | No table cell exceeds one clause |
| Evidence | Every factual claim has a file:line, test, or command |
| Terms | Every term in the terms table is used with that meaning only |
| Paths | `設計` states the normal, degraded, and boundary paths |
| Gaps | Every place `設計` follows existing code instead of a real constraint has a row in `現狀落差` with one decision |
