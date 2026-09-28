# Retrieval failure diagnosis (baseline-dense, book-filtered, top 5)

27 of 40 scored questions miss `full_recall@5` (at least one evidence piece not in the top 5). Ranks are from `eval/gold_ranks.csv`; multiple numbers = multiple evidence pieces, in evidence order.

| id | type | best rank(s) | bucket | notes |
|---|---|---|---|---|
| sh-02 | factual | 6 | ranked low | "Swamp adder" mention ranks just behind other Speckled Band passages using generic snake/whistle imagery. |
| hod-04 | factual | 9 | ranked low | "Exterminate the brutes" is a postscript inside a long paragraph about Kurtz's report; other Kurtz-report content ranks ahead. |
| pp-03 | factual | 10 | ranked low | Collins/Charlotte engagement scene ranks behind other Collins-adjacent passages. |
| hod-05 | factual | 11 | ranked low | Heads-on-stakes scene ranks behind other Kurtz-station description. |
| pp-05 | factual | 11 | ranked low | Wickham/Lydia elopement letter ranks behind other letters in the same chapter. |
| sh-05 | factual | 11 | ranked low | Tunnel explanation ranks behind earlier scene-setting in the same story. |
| pp-04 | factual | 12 | ranked low | Lady Catherine's demand competes with other chapter-56 Darcy dialogue. |
| hod-08 | named_entity | 5, 13 | ranked low | "Harlequin" piece ranks fine (5); "man of patches" epithet, less literal, ranks lower (13). |
| sh-07 | named_entity | 14 | ranked low | Unmasking scene ranks behind earlier detective discussion of the same case. |
| hod-03 | factual | 15 | ranked low | Helmsman death ranks behind other river-attack passages. |
| sh-09 | named_entity | 16 | ranked low | Burnwell passage ranks behind other Beryl Coronet family-drama content. |
| sh-03 | factual | 17 | ranked low | Ryder's confession ranks behind earlier goose/carbuncle scene-setting. |
| hod-11 | multi_hop | 23, 11 | interpretation gap | "Kurtz praised" piece (23) needs inferring that admiring dialogue counts as praise; heads scene (11) is fine. |
| sh-14 | factual | 31 | vocabulary gap | A short, generic-sounding methodological aphorism embeds weakly against surrounding narrative, despite an exact wording match to the question. |
| hod-09 | paraphrase | 33 | interpretation gap | "Death-haunted... unsettling" requires inferring mood from imagery (silent knitting women) the passage never names as ominous outright. |
| hod-12 | multi_hop | 39, 22 | interpretation gap | "Foreshadow" is inferential — neither piece states the connection explicitly. |
| hod-13 | thematic | 43, 24, 6, 18 | question too broad | Whole-arc question; the worst single piece (43) drags `full_recall` down even though 2 of 4 rank fine. |
| pp-10 | multi_hop | 55, 37 | common-name swamp | Wickham/Darcy content is spread across many similar-sounding chunks in this book; the specific comparison framing doesn't stand out. |
| pp-13 | thematic | 3, 56 | vocabulary gap | Entail piece ranks well (3); the opening aphorism (56) doesn't read as "financial pressure" without inference. |
| pp-08 | paraphrase | 57 | common-name swamp | Same Wickham/Darcy density problem as pp-10. |
| sh-13 | multi_hop | 83, 11 | vocabulary gap | Vincent Spaulding's introduction (83) reads as ordinary character description, not "fabricated identity." |
| hod-10 | paraphrase | 136 | interpretation gap | "Expendable" is an abstract judgment; the passage gives only concrete imagery (starvation, shadows), never states the workers were discarded once useless. |
| sh-12 | multi_hop | 50, 138 | vocabulary gap | Windibank piece (138) shares sh-06's gap below. |
| pp-11 | multi_hop | 118, 238 | common-name swamp | Same Darcy-density issue as pp-10/pp-08, compounded across two pieces. |
| sh-06 | named_entity | 97, 308 | **vocabulary gap (confirmed)** | Probe rewrite ("Holmes catches Windibank by matching his typewriter to the Hosmer Angel letters") ranked **15th** vs. **308th** for the original question wording, on the exact same passage. Wording alone is the gap. |
| pp-12 | thematic | 91, 53, 358, 191, 334 | question too broad | Five-piece whole-novel arc; several pieces individually rank poorly for a summary-style query — expected for this question type. |
| pp-09 | paraphrase | 359, 146 | **vocabulary gap (confirmed)** | Probe rewrite ("she grew ashamed of herself, blind, partial, prejudiced, and absurd") ranked **1st** vs. **359th** for the original question wording, on the exact same passage. Same conclusion as sh-06. |

## Bucket counts

| Bucket | Count |
|---|---|
| Ranked low (rank 6–20) | 12 |
| Vocabulary gap | 8 (2 confirmed by probe rewrite) |
| Interpretation gap | 4 |
| Common-name swamp | 3 (all Pride and Prejudice) |
| Question too broad | 2 (both thematic, whole-arc) |
| Chunking problem | 0 |
| Label error | 0 (fixed in v1→v2 audit) |

## What the probes settled

Two of the worst outliers (pp-09 at rank 359, sh-06 at rank 308) were confirmed as pure vocabulary gaps, not chunking problems: rewriting the question in the book's own words found the *same* passage at rank 1 and rank 15 respectively. The passages and their chunking are fine; dense embedding alone doesn't bridge the gap between an analytical question and the book's own phrasing for these two.

## The Pride and Prejudice cluster

Checked chapter 35's chunking directly (`SELECT ... WHERE chapter_num = 35`): the Wickham portion of Darcy's letter lands in its own distinct child chunks (chunk_idx 6–9), clearly separated from the Jane/Bingley portion (chunk_idx 1–5) — so it is **not** diluted into an unrelated chunk, ruling out that specific chunking hypothesis. The actual cluster (pp-08, pp-10, pp-11) is a genuine common-name swamp: Darcy and Wickham are mentioned constantly throughout the novel, so comparison-style questions about them don't stand out from ordinary narrative mentioning the same names, in embedding space.
