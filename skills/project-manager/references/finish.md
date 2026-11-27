## Builds And Tests

The machine runs a limited number of build and test commands at a time
across all sessions.
Run every build and test command (`cmake --build`, `ninja`, lit, unit tests,
`pytest` over native code) through the build slot, in the background, and
wait for its notification:

```bash
python3 ~/WorkSpace/Notes/tools/pr-triage/build_slot.py --label {{ITEM_LABEL}} -- <command...>
```

It waits while another session holds the slot, and prints who holds it. Do
not run builds outside it, and do not raise `-j` to make up for the wait.

## Finish

Keep the status file `{{STATUS_PATH}}` current while you work; the Projects
page shows it on the item's card and under "Needs you".
Report progress and results only through this file: the manager session
runs on demand and may not be running, so do not send it messages or wait
for it. Put a result the user should read in `step`, or in a file named by
`report`. Write it as JSON:

```json
{
  "state": "implementing",
  "branch": "<the branch you commit to>",
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
| `submitting` | the review is applied and the tests pass again; you commit, push, and open a draft PR | empty; `report` is the review's archived `final.md` |

1. Write `implementing` and `branch` before the first edit. The page finds
   the PR by this branch once it is open.
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
1. When everything is applied and the tests pass, write `submitting` with
   `report`, then commit, push, and open a draft PR without asking the
   user. Follow the repository's commit and PR rules. Check each claim in
   the commit message and the PR description against the diff and the
   commands you ran, then run the `reader-first-writing` cold-reader check
   on the PR description. From here the work does not need the user unless
   it gets stuck, which is `needs_you` again.
1. After the PR is open, record it, which also removes the status file; the
   page then follows the PR on GitHub. The page also finds it by `branch`
   within a few minutes if this step is missed:
   `python3 ~/WorkSpace/Notes/tools/pr-triage/projects.py link-pr {{PROJECT_ID}} {{ITEM_ID}} <number>`.
