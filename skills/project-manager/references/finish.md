## Finish

Keep the status file `{{STATUS_PATH}}` current while you work; the Projects
page shows it on the item's card and under "Needs you". Write it as JSON:

```json
{
  "state": "implementing",
  "step": "Writing the unit tests",
  "questions": [],
  "report": null,
  "updated": "2026-11-25T14:00:00Z"
}
```

| `state` | When | `questions` |
| --- | --- | --- |
| `implementing` | from the first edit until the build and the tests pass | empty |
| `reviewing` | while `cross-agent-review` runs and its findings are applied; `step` names the review step | empty |
| `needs_you` | a question waits for the user | one line per question, each naming its finding or decision |
| `ready_to_commit` | the review is applied and the tests pass again | empty; `report` is the review's archived `final.md` |

1. Write `implementing` before the first edit.
1. When the build and the tests pass, write `reviewing` and run the
   `cross-agent-review` skill on the working-tree diff of the worktree
   against the branch's base. Do not stop to ask whether to run it.
1. Apply the accepted findings as the skill says, and rerun the tests.
1. Each time a question needs the user, write `needs_you` with the question
   in `questions`, then ask it with AskUserQuestion. Questions are:
   `unresolved` rows, a `Design question` or `Optional trade-off` without a
   clear recommendation, and any finding that would change the design. Do
   not change the design in this session: name the design decision the
   finding contradicts, and let the user take it to the design session.
   After the answer, clear `questions` and go back to `reviewing`.
1. When everything is applied and the tests pass, write `ready_to_commit`
   with `report`, then show the user the summary and the diff. Commit, push,
   and open the PR only after the user agrees.
1. After the PR is open, delete the status file; the page then follows the
   PR on GitHub.
