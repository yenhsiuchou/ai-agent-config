# Document Template

Use these sections in this order. Drop a section only when it would be empty,
except `待決定` and `Review 紀錄`, which always stay.

````markdown
# <title>

<problem in one sentence>。<proposed answer in one sentence>。

**狀態（yyyy-mm-dd）**：<draft / in review / reviewed; PRs and their state>

## Recap：<concepts>

## 名詞

| 名詞 | 意思 |
|---|---|

## 問題

<real IR that shows the failure, the command that produced it, and a table
of every known failing input: input / what happens / evidence>

## 設計

<the rule as a table or diagram; one diagram per mechanism; the normal,
degraded, and boundary paths>

## 現狀落差

| 現狀（file:line） | 設計要的 | 決定：先修（prerequisite PR）／隔離在邊界並記成 debt／保留（理由） |
|---|---|---|

## 這次不做

<each item and why it can wait>

## 待決定

<each open decision: the question, the options with their evidence, the
check that would decide it; "無" when empty>

## 改動 / PR 切法

<one row per PR or step: what it changes, how it is verified, what state the
pipeline is in after it>

## 驗證

<tests and probes that show the design works>

## Review 紀錄

| 項目 | 內容 |
|---|---|
| 輪數 | |
| accepted / dropped / unresolved | |
| Archive | |
````
