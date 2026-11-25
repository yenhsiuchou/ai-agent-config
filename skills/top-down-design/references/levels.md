# Levels

Each level asks one kind of question. Answer only the questions of the current
level; note the others in `之後的層`.

## L0 Frame (`frame`)

| Ask | Write |
| --- | --- |
| What goes wrong or is missing, for which stage or user? Show a real failing input. | `問題` with the real IR and command |
| Which limits are real: hardware, external contracts, stated global invariants? | `Invariants` and the project file's `invariants` (id `I1`, `I2`, …; one sentence each) |
| Which current behavior exists only because earlier code was written that way? | `現狀落差`: classify each row now; decide each row in the level that owns it |
| What is true when the design is done? What is out of scope? | the first lines of the document; `這次不做` |
| Which concepts does the user need for this design? | the teaching offer of the Teaching section |

Leave when the user confirms the invariants. An invariant names a rule the
whole design keeps, such as "a pass decides before it changes IR"; a choice
between designs is a decision, not an invariant.

## L1 Ownership (`ownership`)

| Ask | Write |
| --- | --- |
| Which decisions does the feature need? | one row per decision in §1 `誰決定什麼` |
| For each decision: which component owns it, and where does its information first exist? | the owner, the information, the pipeline position |
| Which invariant does each root decision keep? | `serves` |

Typical questions: which pass decides X; whether X is decided early or late;
which existing design this one replaces.

Do not discuss function signatures, data structures, or algorithms here.

## L2 Contract (`contract`)

| Ask | Write |
| --- | --- |
| What does each owner guarantee to the next component? | §2, one row per contract: `C1`, `C2`, … with the guarantor |
| What happens when the guarantee cannot be met: skip, error, fallback? | the failure behavior of each contract |
| Where is the atomic boundary: what is checked before IR changes, and why can the change not fail after the check? | the decide/apply split |
| Which existing API is reused, and which needs a new entry point? | the API decision |

Use the design principles of
`../system-design-review/references/design-principles.md`: atomic-transition,
decide-equals-apply, single-owner, guarantee-at-source.

## L3 Mechanism (`mechanism`)

| Ask | Write |
| --- | --- |
| What rule or algorithm does each owner run? | §3, one diagram per mechanism |
| What happens on the normal, degraded, and boundary paths? | `各種路徑` table: path / case / result |
| Which inputs from real workloads exercise each path? | measured counts with the command |

## L4 PR Split (`split`)

| Ask | Write |
| --- | --- |
| Which PRs implement the contracts? One contract boundary per PR when possible. | `改動 / PR 切法`, and one project item per PR with `depends_on` |
| What state is the pipeline in after each PR? | the table column "之後 pipeline 的狀態" |
| How is each PR verified? | `驗證` and the tests per PR |

Run `projects.py sync` after adding the items.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Deciding an API shape in L1 | Note it in `之後的層`; decide it in L2. |
| A contract decision that silently changes an owner | Reopen the L1 decision. |
| A mechanism decision recorded before its contract | Wait; `check` warns "the current step … is not frozen yet". |
| Re-reviewing the whole document after each change | Review only the current level; the whole document is reviewed once at the end. |
