# Document Skeleton

The document follows `../../cross-agent-design-doc/references/doc-style.md`
and the section order of
`../../cross-agent-design-doc/references/doc-template.md`, with two changes:
`Invariants` follows `問題`, and `設計` is split by level. Each level fills its
own sections; a section of a later level stays `（L<n> 未開始）` until then.

````markdown
# <title>

<problem in one sentence>。<answer in one sentence, once L1 is frozen>。

**狀態（yyyy-mm-dd）**：<current level; frozen levels>

## Recap：<concepts>

## 名詞

| 名詞 | 意思 |
|---|---|

## 問題                                   <!-- L0 -->

## Invariants                             <!-- L0 -->

| # | 規則 | 來源 |
|---|---|---|

## 設計

### 1. 誰決定什麼                          <!-- L1: owners and decision cards -->

### 2. Contracts                          <!-- L2: C1… and decision cards -->

### 3. 機制                                <!-- L3: rules and decision cards -->

### 各種路徑                               <!-- L3 -->

## 現狀落差                                <!-- classified in L0, decided in the owning level -->

## 之後的層                                <!-- questions noted for a later level -->

## 這次不做

## 待決定                                  <!-- reopened or unresolved decisions -->

## 改動 / PR 切法                          <!-- L4 -->

## 驗證                                    <!-- L4 -->

## Review 紀錄                             <!-- one row per level review and the final review -->
````

Keep a decided card in its section with its choice marked; remove the options
that lost only when the document gets long, and keep their one-line reason in
`Review 紀錄`.
