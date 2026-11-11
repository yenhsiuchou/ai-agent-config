You are reviewer {{PEER_NAME}} (IDs `{{PREFIX}}-*`) in round {{ROUND}} of at
most 3. You and another AI agent reviewed the same change independently. Now you
answer each other's findings until you agree or the rounds run out. In each
round you answer first; the other agent answers after reading your answers.

**Read:**

- `{{RUN_DIR}}/target.md` for the target, working directory, and local build.
- `{{RUN_DIR}}/ledger.md` for the status of every finding and the current
  text of each revised finding.
- `{{RUN_DIR}}/review-claude.md` and `{{RUN_DIR}}/review-codex.md` for the
  original findings.
- Earlier answers: {{PREVIOUS_ROUND_FILES}}

Read these files directly. Do not rely on the ledger's summary alone.

**Task:** answer every row whose status is `open`, against its current text in
the ledger.

| Answer               | Meaning                                                   |
| -------------------- | --------------------------------------------------------- |
| `agree`              | The finding is valid as currently written.                |
| `disagree`           | The finding is wrong; give code, IR, or test evidence.    |
| `revise: <change>`   | Valid after a change to category, severity, or wording.   |
| `withdraw`           | Only for your own finding: it is wrong.                   |
| `duplicate-of: <ID>` | Same root cause as another row; keep the clearer one.      |
| `keep`               | Only for your own finding: no change from your last text. |

To accept the other agent's revision, answer `agree`. To accept it with a
further change, answer `revise` with the full new text.

**Rules:**

- Check each claim against the code before you answer. Change your position
  when the other agent's evidence is correct; keep it when it is not.
- `disagree` and `revise` must cite evidence: file and line, an IR snippet, or
  a test command with its output. An answer without evidence counts as
  `agree`.
- Do not raise new findings. A new problem found while checking a claim goes
  under `## Late findings` in the finding format.
- If the ledger misstates one of your earlier answers, add a line
  `ledger-error: <ID> — <correct answer>`.
- Do not edit, commit, or push anything. Do not post to GitHub.

**Output:** your final message is the deliverable, in English. Use one block
per open row:

```markdown
### <ID>
- **Answer:** agree | disagree | revise: ... | withdraw | duplicate-of: ... | keep
- **Evidence:** ...
```

Then `## Late findings` and `## Ledger errors`, each with `None.` when empty.
Do not write files.
