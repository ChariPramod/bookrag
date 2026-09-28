# Baseline: dense-only retrieval (v0.1-baseline)

Config: `configs/baseline.yaml` — BGE-M3 embeddings, pgvector HNSW (cosine), parent/child chunking (2000/300/40 tokens). Eval set: `eval/questions_v2.jsonl` (40 scored questions across 3 books, audited — see `eval/CHANGELOG.md`). Recorded in Langfuse under dataset `book-rag-golden-v2` (filtered, unfiltered, exact-scan runs) and locally in the `eval_runs` table.

## Overall (book-filtered)

| metric | @1 | @5 | @10 | @20 |
|---|---|---|---|---|
| recall (any evidence piece) | 0.200 | 0.375 | 0.475 | 0.725 |
| full_recall (every piece) | 0.200 | 0.325 | 0.400 | 0.625 |

MRR (reciprocal rank): **0.296**

Unfiltered (searching across all 3 books, no book restriction) is nearly identical: recall@5 0.375, full_recall@5 0.325, MRR 0.289 — the book filter isn't doing much work yet at only 3 books, as expected; it will matter more once distractor books are added in Stage 3.

## Per type (book-filtered)

| type | n | recall@5 | full_recall@5 | recall@20 | full_recall@20 | MRR |
|---|---|---|---|---|---|---|
| factual | 16 | 0.375 | 0.375 | 0.938 | 0.938 | 0.366 |
| named_entity | 9 | 0.667 | 0.556 | 0.889 | 0.889 | 0.537 |
| paraphrase | 6 | 0.333 | 0.333 | 0.333 | 0.333 | 0.075 |
| multi_hop | 6 | 0.000 | 0.000 | 0.333 | 0.000 | 0.030 |
| thematic | 3 | 0.333 | 0.000 | 0.667 | 0.000 | 0.167 |

## Per book (book-filtered)

| book | n | recall@5 | full_recall@5 | recall@20 | full_recall@20 | MRR |
|---|---|---|---|---|---|---|
| Heart of Darkness | 13 | 0.385 | 0.308 | 0.769 | 0.615 | 0.325 |
| Pride and Prejudice | 13 | 0.385 | 0.308 | 0.615 | 0.538 | 0.278 |
| The Adventures of Sherlock Holmes | 14 | 0.357 | 0.357 | 0.786 | 0.714 | 0.285 |

Roughly even across books — no single book is dragging the average down. Pride and Prejudice has the weakest `recall@20` (0.615), consistent with the common-name swamp finding below.

## Gold rank distribution (57 evidence pieces, `eval/gold_ranks.csv`)

| Rank bucket | Count | Meaning |
|---|---|---|
| 1–5 | 15 | Working |
| 6–20 | 16 | Found but ranked low |
| 21–100 | 16 | Close, just outside the net |
| 100+ | 10 | Question and passage are far apart in embedding space |

The 100+ cluster concentrates in Pride and Prejudice (7 of 10: 2 paraphrase, 2 multi_hop, 3 thematic pieces) — the common-name swamp and whole-arc thematic questions are the same phenomenon showing up twice.

## Failure buckets (27 questions miss full_recall@5 — see `eval/failures.md` for the full table)

| Bucket | Count | Example |
|---|---|---|
| Ranked low (6–20) | 12 | sh-02: "swamp adder" mention ranks 6th behind other Speckled Band passages using generic snake imagery |
| Vocabulary gap | 8 | sh-06: probe rewrite in the book's own words ranked the *same passage* 15th vs. 308th for the original question |
| Interpretation gap | 4 | hod-10: "expendable" is an abstract judgment the passage never states outright, only shows in concrete imagery |
| Common-name swamp | 3 | pp-08/pp-10/pp-11: Darcy and Wickham are named constantly throughout the novel, so comparison questions about them don't stand out |
| Question too broad | 2 | pp-12: five-piece whole-novel arc question; several pieces individually rank poorly for a summary-style query |
| Chunking problem | 0 | Checked directly: chapter 35's Wickham content sits in its own distinct chunks, not diluted into the Jane/Bingley part |
| Label error | 0 | Fixed in the v1→v2 audit (13 questions corrected — see `eval/CHANGELOG.md`) |

## HNSW vs. exact scan

Identical top-20 results for all 40 scored questions with `hnsw.iterative_scan = relaxed_order` and `ef_search = 100`. HNSW loses nothing at this corpus size (1,429 vectors). This also settles that the small rank differences seen between filtered and unfiltered runs come from the book filter changing the candidate pool, not from index approximation.

## Conclusions

Named-entity and factual questions work reasonably well (recall@20 approaching 0.9), confirming the pipeline's mechanics — chunking, embedding, and search — are sound; the two confirmed vocabulary-gap cases (pp-09, sh-06) show the *passages* are fine and retrievable, just not by these specific question phrasings under dense search alone. Paraphrase, multi-hop, and thematic questions are the real weak points, and the failure analysis says why: dense embeddings don't bridge the vocabulary/interpretation gap for abstract questions, can't satisfy two-piece evidence with one query vector, and get lost in the common-name swamp for Pride and Prejudice specifically. None of this is a chunking or gold-label problem — both were checked directly and ruled out. The next phase (BM25 and hybrid search) should target the vocabulary-gap and common-name cases specifically, since exact keyword matching is precisely what dense embedding is weak at here; reranking is the more likely fix for multi-hop and thematic, since those need a wider net (bigger top-k) before a cross-encoder can sort the pieces into the top 5.
