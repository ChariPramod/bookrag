# Baseline: dense-only retrieval (v0.1-baseline-audited)

Config: `configs/baseline.yaml` — BGE-M3 embeddings, pgvector HNSW (cosine, `strict_order` iterative scan), parent/child chunking (2000/300/40 tokens). Eval set: `eval/questions_v2.jsonl` (40 scored questions across 3 books, audited twice — see `eval/CHANGELOG.md`). Recorded in Langfuse under dataset `book-rag-golden-v2` (filtered, unfiltered, exact-scan runs) and locally in the `eval_runs` table.

## Overall (book-filtered)

| metric | @1 | @5 | @10 | @20 |
|---|---|---|---|---|
| recall (any evidence piece) | 0.225 | 0.400 | 0.500 | 0.750 |
| full_recall (every piece) | 0.200 | 0.325 | 0.400 | 0.625 |

MRR (reciprocal rank): **0.320**. Unfiltered: recall@5 0.400, full_recall@5 0.325, MRR 0.314 — nearly identical to filtered, as expected at only 3 books; the book filter isn't doing real work yet.

`ann_recall@20` (fraction of HNSW's top-20 also in an exact scan's top-20): **1.0 mean, 1.0 min** across all 40 questions. HNSW loses nothing at this corpus size.

## Per type (book-filtered)

| type | n | recall@5 | full_recall@5 | recall@20 | full_recall@20 | MRR |
|---|---|---|---|---|---|---|
| factual | 16 | 0.375 | 0.375 | 0.938 | 0.938 | 0.366 |
| named_entity | 9 | 0.667 | 0.556 | 0.889 | 0.889 | 0.537 |
| paraphrase | 6 | 0.333 | 0.333 | 0.333 | 0.333 | 0.075 |
| multi_hop | 6 | 0.167 | 0.000 | 0.500 | 0.000 | 0.192 |
| thematic | 3 | 0.333 | 0.000 | 0.667 | 0.000 | 0.167 |

## Per book (book-filtered)

| book | n | recall@5 | full_recall@5 | recall@20 | full_recall@20 | MRR |
|---|---|---|---|---|---|---|
| Heart of Darkness | 13 | 0.385 | 0.308 | 0.769 | 0.615 | 0.325 |
| Pride and Prejudice | 13 | 0.385 | 0.308 | 0.615 | 0.538 | 0.278 |
| The Adventures of Sherlock Holmes | 14 | 0.429 | 0.357 | 0.857 | 0.714 | 0.354 |

Roughly even — no single book drags the average down. Pride and Prejudice has the weakest `recall@20` (0.615), consistent with the common-name swamp finding below.

## Gold rank distribution (57 evidence pieces, `eval/gold_ranks.csv`)

| Rank bucket | Count | Meaning |
|---|---|---|
| 1–5 | 16 | Working |
| 6–20 | 16 | Found but ranked low |
| 21–100 | 16 | Close, just outside the net |
| 100+ | 9 | Question and passage are far apart in embedding space |

The 100+ cluster still concentrates in Pride and Prejudice — the common-name swamp and whole-arc thematic questions are the same phenomenon showing up twice.

## Failure buckets (27 questions miss full_recall@5 — see `eval/failures.md`)

| Bucket | Count | Example |
|---|---|---|
| Ranked low (6–20) | 12 | sh-02: "swamp adder" mention ranks 6th behind other Speckled Band passages using generic snake imagery |
| Vocabulary gap | 8 | sh-06/pp-09: probe rewrites in the book's own words ranked the *same passages* 15th and 1st vs. 308th and 359th for the original question phrasing |
| Interpretation gap | 4 | hod-10: "expendable" is an abstract judgment the passage never states outright, only shows in concrete imagery |
| Common-name swamp | 3 | pp-08/pp-10/pp-11: Darcy and Wickham are named constantly throughout the novel, so comparison questions about them don't stand out |
| Question too broad | 2 | pp-12: five-piece whole-novel arc question; several pieces individually rank poorly for a summary-style query |
| Chunking problem | 0 | Checked directly: chapter 35's Wickham content sits in its own distinct chunks, not diluted into the Jane/Bingley part |
| Label error | 0 | Fixed across two audit passes (v1→v2, then a follow-up correction — see `eval/CHANGELOG.md`) |

## HNSW: relaxed_order vs strict_order vs exact scan

Directly compared, at the individual chunk-id level (not just paragraph range, since several chunks in this corpus share a paragraph range and could mask a real difference), `hnsw.iterative_scan = relaxed_order` returned results in **identical order** to a forced exact scan for all 40 questions. No evidence of relaxed_order costing anything here. The store now uses `strict_order` anyway — the theoretical risk (relaxed_order trades strict distance ordering for better recall under filtering) is real at larger corpus sizes even where it isn't manifesting yet, and `ann_recall@20` is now a permanent metric in `scripts/eval.py` to catch it early if it ever does regress.

## Known limitation: no single-query technique fixes multi-hop or thematic

Not one multi-hop or thematic question gets `full_recall@20` — every one of the 9 multi-hop/thematic questions requires 2+ evidence pieces, and no single query vector pulls results from more than one "region" of meaning at once. This is structural, not a chunking, labeling, or index-tuning problem: hybrid search (BM25 + dense) would help the vocabulary-gap cases, and reranking would help sort a wider candidate pool, but neither changes what a *single* query embedding can retrieve in one pass. The eventual fix is query decomposition — splitting a multi-hop question into sub-questions and searching each separately — which is out of scope for this stage. Recorded here so it isn't mistaken for a regression when hybrid search and reranking land without moving these numbers much.

## Conclusions

Named-entity and factual questions work well (recall@20 approaching 0.9), confirming the pipeline's mechanics are sound. The confirmed vocabulary-gap cases (pp-09, sh-06) show retrievable passages failing purely on question phrasing, not chunking or labeling — both were checked and ruled out directly. A follow-up correction (adding `[3,125]` to sh-06/sh-12/sh-13's evidence, per external review) meaningfully improved those three questions' ranks without changing the overall miss count, underscoring that label quality moves individual results by as much as a retrieval-method change would. Paraphrase, multi-hop, and thematic remain the weak points: BM25/hybrid search is the next lever for the vocabulary-gap and common-name-swamp cases specifically, reranking is the likely fix for pushing ranked-low results into the top 5, and multi-hop/thematic will need query decomposition later — not something this stage's changes will move.
