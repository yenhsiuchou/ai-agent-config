---
name: direct-instruction
description: >-
  Teach a technical topic deeply through a tailored, persistent course with a
  concept dependency map, source-backed self-contained materials, and
  diagnostic questions that test reasoning. Use when the user asks to learn or
  deeply understand a technical concept; not for a quick factual answer or
  market research.
---

# Direct Instruction

Help the learner use a concept to reason, predict, compare designs, and know
its limits—not merely repeat its definition.

Use this skill for a multi-turn technical learning course. Keep its state in
the learner's chosen working directory so it can resume in later sessions. If
no directory is specified, use the current workspace.

## Course State

1. Identify the topic and form a `snake_case` slug, such as
   `speculative_decoding`.
2. Look for `[slug]_session.md` in the chosen directory.
   - If present, follow **Resume A Course**.
   - If absent, follow **Start A Course**.

Use these files:

- `[slug]_session.md`: learner background, dependency map, status, and next
  action.
- `[slug]_notes.md`: references and durable knowledge notes.
- `[slug]_qa.md`: question-and-answer record.
- `[slug]_material_index.md`: material index.
- `[slug]_material_ch00_overview.md`: course map.
- `[slug]_material_chNN_[concept].md`: one concept's material.

Do not create files until the learner confirms the intended directory when the
current workspace is not clearly appropriate.

## Start A Course

### Interview Naturally

Do not ask every question at once. Learn enough to tailor the course:

- prerequisite knowledge;
- goal: implementation, research, or conceptual understanding;
- desired depth: overview or independent derivation;
- scrutiny level:
  - **quick**: one or two evidence checks; directionally correct is enough;
  - **standard**: two or three checks across dimensions, including transfer;
  - **deep**: continue until the learner can reason with the mechanism.

Summarize the learner model in two or three sentences and ask for confirmation
before designing the course.

### Build The Concept DAG And Research It

Make each node independently teachable and assessable, normally requiring
30–60 minutes of reading. Use five to ten nodes unless real complexity calls
for a different size. Draw `A -> B` when B requires A.

`ch00_overview` is the sole root and every concept depends on it. Mark concepts
already known by the learner `understood`; mark the rest `not_exposed`.

Before writing material, browse for each concept. Prefer original papers,
official documentation, specifications, and source repositories. Use technical
articles only when primary material cannot explain the point. Record useful
sources in `## References` in `[slug]_notes.md`. Never present uncertain detail
as fact; mark it `⚠️ Needs verification`.

### Create Initial Files

Create the state files, material index, and Ch00. Do not prewrite later chapter
materials. The learner reads Ch00 before any detailed chapter.

## Resume A Course

Read the session file. Select the first concept whose status is neither
`understood` nor `can_apply` and whose prerequisites are all `understood`.
Check `## Next Action`, then say in one sentence what happens next.

## Ch00: Overview Map

Ch00 gives the learner a map before details: components, their connections, and
why the design follows from constraints.

- Use mostly diagrams, normally three to six. A diagram expresses one
  information axis.
- Separate **structure** (connections), **time** (ordering), and **space**
  (layout or range). Split diagrams that need artificial edges to combine them.
- Reuse one minimal, complete example throughout the map.
- Start with a table mapping sections to the chapters that explain them.
- Before any new material, recap every concept the course builds on that the
  learner already knows (nodes marked `understood` and assumed background).
  Keep each recap short: what it is, the rule or mechanism in one small code
  or formula block, and the case it handles or rejects. The recap fixes the
  shared vocabulary that the new material then changes or extends. When the
  topic changes an existing mechanism (for example, a PR), recap the current
  behavior first; this is the baseline, not history. Title the section
  `Recap: <the concepts recapped>`, not a generic label, and do not add a
  sentence that announces what the recap is for.
- After every figure, state relevant design choices and reasons. Exclude
  historical versions, old bugs, review findings, and project evolution.
- End with Key Formulas and a Glossary.

Ask exactly one mechanism-reconstruction question after the learner reads Ch00,
unless they have already supplied equivalent reasoning. Confirm the high-level
model only. If it passes, mark `ch00_overview` `understood`.

Ch00 is living material. Update it when later teaching changes a system-level
fact.

## Teaching Loop

For every concept, complete: research → material → source audit → learner reads
→ assess evidence or ask diagnostics → update state.

### Research And Material

1. Browse accurate material and append sources to `[slug]_notes.md`.
2. Before drafting, state the learner-facing contract: one question it answers,
   input, output, and one normal success or failure example. Split or reorder a
   concept that cannot be stated without unknown terms.
3. Write `[slug]_material_chNN_[concept].md`. It must be self-contained. Follow
   the order in Presentation Style: what the chapter does, a short recap of the
   known concepts it depends on (so the learner and the material share terms),
   then the concrete need, the contract, and the method or math.
   State boundaries, misconceptions, and where analogies fail. Mark uncertainty
   with `⚠️ Needs verification`.
4. Audit material against recorded sources before giving it to the learner:
   - verify factual claims, calculations, examples, code, and IR;
   - explain every term before it is needed;
   - ensure diagrams agree with text and keep information axes separate;
   - ensure the opening explains the problem, output or decision, and why the
     first example succeeds or fails;
   - defer implementation detail not required to understand the contract; and
   - correct only claims supported by sources or direct verification.
5. Run the `reader-first-writing` cold-reader check before marking material
   `material_ready`. When a subagent mechanism is available, use a fresh,
   read-only reviewer. Give it only the material, learner background,
   prerequisites, and source paths; do not provide authoring conversation or an
   intended answer. It reports factual gaps, unclear steps, diagram/text
   conflicts, and incorrect examples. Verify each finding before editing. Run
   at most one re-review. If independent review is unavailable, self-check and
   record that it was not independent.
6. Record `Source audit: N issues found, M corrected` and `Cold-reader check:
   ...` in related notes. Do not claim an independent review that did not occur.
7. Tell the learner material is ready and wait until they say they have read it.
   Do not begin questions before that confirmation.

### Assessment Evidence And Diagnostic Questions

Questions verify and reinforce understanding; they must not be the first place
new knowledge is taught. Natural conversation can be evidence.

Count a learner message as evidence only when it correctly does at least one:

- reconstructs a causal mechanism or control flow;
- applies it to a concrete example;
- predicts a changed condition or boundary case; or
- compares alternatives with a causal trade-off.

An assertion such as "I understand" or a paraphrased definition alone is not
evidence.

For `quick` and `standard`, natural evidence may satisfy checks. Ask the
smallest targeted question only when an essential dimension is unproven, a
reasoning gap exists, or the next concept needs an unverified capability. For
`deep`, actively probe missing dimensions.

If the learner asks to advance before enough evidence exists, honor the pace but
record that the concept advanced without diagnostic confirmation.

Choose different dimensions:

| Dimension | Checks |
|---|---|
| Transfer | Apply the mechanism in a new setting |
| Counterfactual prediction | Predict a changed condition |
| Boundary condition | Identify where it fails or becomes trivial |
| Comparative reasoning | Explain a design trade-off |
| Mechanism reconstruction | Rebuild the causal chain without notes |

Never ask fact-recall-only questions. Assess evidence or answers immediately:

- **understood**: correct causal direction and key mechanism;
- **partial**: name the missing link, direct the learner to material, and ask
  them to reason again;
- **missed**: identify incorrect reasoning, direct a reread, then ask again.

Do not give the answer in chat for `partial` or `missed`; material remains the
source of new knowledge. If a learner finds unclear or incorrect material,
correct it using sources, request a reread, then resume assessment. Rewrite a
chapter's causal flow rather than appending local clarification when the learner
cannot state its problem, output, or section connection.

### Update State

After a concept passes natural evidence or diagnostics:

1. update its status and `## Next Action` in `[slug]_session.md`;
2. add a concise `## Verification Summary` entry;
3. regenerate the session DOT graph with status colors;
4. append the evidence or diagnostic exchange to `[slug]_qa.md`;
5. add a distilled concept note to `[slug]_notes.md`;
6. update the material index; and
7. update Ch00 if the system-level explanation changed.

## Material Conventions

Use English for file titles, section headings, metadata labels, table headers,
diagram text, and status values. Write pedagogical prose in the learner's
language. Keep code and technical terms in English where clearer.

### Presentation Style

Lead with pictures, not prose. A chapter whose core argument is a wall of text
must be rewritten before the learner reads it.

- **Reading time ≤ 20 minutes.** Split a concept that needs more.
- **Open every chapter with `## What This Chapter Does`**, before the recap:
  the one question the chapter answers, the high-level concept in one or two
  sentences (the intuition the rest of the chapter makes precise), and where
  it sits in the course and in the learner's goal (for a PR review: which
  review decision it enables). Short chapters still need this.
- **Order**: purpose → recap → one concrete reject or failure case drawn as a picture →
  one accept case → the rule in three lines → why the rule holds (a DOT flow of
  premises to conclusion, plus a short "missing it breaks because" table) →
  the few code lines that implement it → a table of worked cases →
  boundaries as bullets.
- **Descriptive headings.** In every chapter, including Ch00, title each
  section and figure by what it shows (for example, "Writes To One Element:
  Same Order Before And After"), never "Fig N". Cross-references use the title.
- **Explain with index expressions.** For an access or layout, give a table of
  result dim → expression → which loop it pins, then draw the iteration grid
  with the element each cell touches. Keep prose to the sentence each figure
  needs.
- **Real IR only**, trimmed, produced by the actual binary.
- **Interactive explorer** when the concept is "change a choice, watch the
  outcome" (loop order, cut choice, packet flow). Embed it inline in the
  Markdown, and read `references/interactive-explorer.md` before building
  one.

Use this chapter shape when it fits:

````markdown
# ChNN: [Concept Name]

> **Reading time**: ~N minutes (≤ 20)
> **Prerequisites**: ChNN or none

## What This Chapter Does
## Recap: [the concepts recapped]
## [Reject case, titled by what it shows]
## [Accept case, titled by what it shows]
## The Rule
## Why The Rule Holds
## Implementation
## Worked Cases
## Boundaries And Misconceptions
## References
````

Choose diagrams by information axis:

| Axis | Preferred format |
|---|---|
| Structure: components and links | Graphviz DOT |
| Time: ordering, overlap, state change | Mermaid sequence, gantt, or state diagram |
| Space: linear or grid arrangement | ASCII section diagram |
| Precise geometry | Embedded SVG |

Use DOT for flow layout, tables for comparison and responsibility, and ASCII
for large grids. For DOT, use `bgcolor=transparent`, `shape=box`,
`style="rounded,filled"`, and `fontname="Helvetica"`. Use `rankdir=TB` for a
process and `LR` for an interface. Keep labels ASCII English and explain each
diagram directly below it.

## End A Session

End when the learner asks to stop or after two or three concepts. Ensure
`Next Action` is current, then say what was learned and where the course will
resume. Do not generate an extra deliverable unless requested.

Before ending, confirm Ch00 exists and is current; every taught concept has
sources, self-contained material, a source audit, varied diagnostics, updated
DAG/status/index/notes/QA, and a concrete next action.
