---
name: review-comment-drafting
description: Draft inline review comments for another author's PR from findings the user picked, in the user's house style (short English questions, one concern each), show them for approval, and post them only when told to. Use when the user asks to draft, write, shorten, soften, or post review comments or inline comments on someone else's PR, including after cross-agent-review, system-design-review, or review-pr.
---

# Review Comment Drafting

A review comment asks the author one question about one place in the diff. The
author should understand it without reading our review notes, and decide the
fix themselves.

This skill covers comments on another author's PR. For replies on the user's
own PR, follow the `pr` skill or `reader-first-writing` instead.

## Step 1: Pick the Findings

Draft only the findings the user picked. If the user did not pick, propose a
short list and say which findings you left out and why. Then drop:

- a finding the PR title, description, or an existing thread already answers.
  Read the description and every existing review thread
  (`gh api repos/{owner}/{repo}/pulls/<n>/comments` and `.../reviews`) first;
- a finding you cannot show on real IR, a test, or a concrete input;
- a finding about a pre-existing problem that the PR only moves;
- a finding that belongs to another component, such as a later pass that
  already handles the case. Check that the problem is this PR's job before you
  ask the author to change it.

A short list, or an empty one, is a good result.

## Step 2: Write Each Comment

Write in simple English, even when the discussion is in Chinese.

**Shape.** One concern per comment, anchored to the diff line it is about:

1. One sentence on what the code does here, in code names.
1. The concrete case: a trimmed IR snippet, a test name, or an input such as
   `` `%m[%j, %i] = %a[%i, %j]` ``. Put a long reproducer in a
   `<details><summary>Input</summary>` block.
1. A question.

A test request can be the question alone: "Should we add a test with a strided
access, such as `sml.load %in[0, 0, %i * 2]`, for this decline?"

**Tone.** Ask; do not judge. Use question forms such as "Could …?",
"Should …?", "Is that case intended?", "Would it be worth …?". When you name a
fix, offer it as one option ("Could this be one plan result, for example
`widensWithoutRebuild`?"), not as the required change. Start a minor point
with `Nit:` or `Optional:`. A short "Nice that …" is fine when it is true.

**Length.** Two to four sentences, plus the snippet. Every sentence must help
the author act. Cut:

- proof of our work, such as "I ran these cases against main";
- schedule advice, such as "This could be a follow-up before the stack reaches
  main";
- a reference to another PR or doc that the author does not need for this
  question;
- severity labels, consensus labels, agent or finding IDs (`CL-2`, `CX-1`),
  and internal design-doc section names;
- a repeat of what the description already says.

**Design-doc PRs.** Write as a reader who has read only the doc. Do not cite
code facts that the doc does not mention; turn them into a question the doc
raises. Drop a point that a general rule in the doc already covers. Raise an
implementation problem on the implementation PR, with an IR reproducer, not on
the doc PR.

**Replies to the author.** When the author has answered a comment, read the
whole thread and the current diff first. If the answer resolves the point, a
short acknowledgement or no reply is enough. Otherwise ask one follow-up
question in the same thread; do not repeat the original argument.

## Step 3: Show the Draft

Show every comment to the user before anything goes to GitHub. For each
comment, give:

- `path:line` and the code on that line;
- the English comment exactly as it would be posted;
- one line in Chinese that says what the comment asks.

Do not show a review body. List any finding whose line is not in the diff
separately, and say that it cannot be posted inline.

When the user asks for a change, change only that comment and show the result.

## Step 4: Post Only When Told

"Draft", "show me", "印出來", "寫一版", and approval of the text ("好", "可以")
do not mean post. Post only after an explicit post request, such as "掛上去",
"貼上去", "post it", or "幫我發".

- **Default: pending review.** POST to
  `repos/{owner}/{repo}/pulls/<n>/reviews` with `commit_id` (the PR head SHA)
  and `comments`, and **no `event` and no `body`**. A body set on a pending
  review is discarded when the user submits.
- **Submit only when the user says so** ("直接送", "submit", "發出去"): then
  set `event: "COMMENT"`, unless the user names `APPROVE` or
  `REQUEST_CHANGES`.

Write the payload to a JSON file and post it with `gh api ... --input <file>`.
Check the response state (`PENDING` or `COMMENTED`) and the comment count, then
tell the user where to find the comments.

**Replies to an existing thread** cannot go through the REST review endpoint,
and the REST `.../comments/<id>/replies` endpoint publishes at once. Use
GraphQL instead:

1. Find the thread id: query `pullRequest.reviewThreads` for the thread whose
   first comment is the one you answer.
1. Use the user's pending review if one exists (`pullRequest.reviews` with
   `states: PENDING`); otherwise create one with `addPullRequestReview` and no
   `event`.
1. Add the reply with `addPullRequestReviewThreadReply`, passing
   `pullRequestReviewId` and `pullRequestReviewThreadId`.

The reply then stays pending with the other comments until the user submits.

Never edit or delete a posted comment without a request for that comment.
