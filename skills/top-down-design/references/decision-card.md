# Decision Card

Write one card per decision in the document's section of its level, before
asking the user:

```markdown
#### D3：<question in one sentence>

服務：I1（<invariant text>）　建立在：D1

| 選項 | 做法 | 證據 | 代價 |
| --- | --- | --- | --- |
| A（建議） | … | file:line、probe 的指令和結果 | … |
| B | … | … | … |

建議 A：<one or two sentences: which invariant it keeps and B does not>
```

- Give two or three options. Each one must be buildable; drop an option that
  breaks an invariant, and say why in one line.
- Put evidence in every row; mark a claim without evidence `未查證`.
- Ids: `D<n>` for decisions; contracts of L2 may use their contract id
  (`C1`). Never reuse an id.

## Asking With AskUserQuestion

| Card | AskUserQuestion |
| --- | --- |
| question | `question`, with the decision id first: "D3：…？" |
| level | `header`, such as "L1 owner" |
| option A (recommended) | first option, label ending in "(Recommended)", description = 做法 and 代價 |
| options B, C | the next options |
| concept the card needs | last option "先教我 <concept>", description "暫停這個決定，用直接教學法教完再問" |

Use `preview` when the options differ in IR or code: show the trimmed IR of
each.

## In The Project File

```yaml
  - id: D3
    level: ownership
    serves: [I1]                 # required on a root decision
    question: Who retypes a template chain to packet storage
    status: proposed             # decided after the user chooses
    choice: <the chosen option in one sentence, once decided>
    date: 2026-11-25             # the day it was decided or revalidated
    depends_on: [D1]
    learn: [../docs/X/course/x_material_ch02_alias.md]   # chapters taught for it
    note: <why an earlier choice changed, if it did>
```
