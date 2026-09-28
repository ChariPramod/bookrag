# Gold answers are evidence pieces, not a flat paragraph list

`gold` (a flat `[[ch,p], ...]` list) became `evidence`: a list of pieces, where each piece is itself a list of `[ch,p]` pairs, and a piece counts as found if *any* one of its paragraphs is retrieved.

## Why

A flat list conflates two different situations that need different scoring. Sometimes several paragraphs are one scene split by chunking (Kurtz's heads-on-stakes spans `[3,4]` and `[3,5]`) — retrieving either one is a full hit. Other times several paragraphs are genuinely separate facts a multi-hop question needs (`[1,58]` Kurtz praised, `[3,4]`/`[3,5]` the heads scene) — a real answer needs both. Scoring "any paragraph found" against the second case makes multi-hop and thematic questions look easier than they are; scoring "all paragraphs found" against the first case makes single-scene questions look harder than they are, since chunking could split that scene differently on any rerun.

Evidence pieces let both readings coexist: `recall@k` (any piece found) and `full_recall@k` (every piece found) are computed from the same data. For single-piece questions the two numbers are identical, so nothing is lost; for multi-hop and thematic questions, `full_recall` becomes the honest number to watch.
