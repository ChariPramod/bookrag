# Parent/child chunking at 2000/300/40 tokens

**Status:** accepted as a starting point, pending experiments (not a settled decision).

Chunking splits each chapter into parents (whole-paragraph groups, chapter-bounded, up to 2000 tokens — read as LLM context, never searched directly) and children (what's actually embedded and searched, packed to 300 tokens with 40 tokens of overlap carried forward between consecutive children). A paragraph that fits the 300-token child budget is packed as one unit; one that doesn't falls back to sentence-level units, so a child boundary lands on a sentence rather than mid-sentence.

## Why these numbers, and why they're not trustworthy yet

2000/300/40 came from the tutorial that specified this project stage, not from tuning against this project's own eval set. On the current 3-book corpus (1,429 children), children average 239 tokens with a max of 335 — that confirms the packing logic behaves as designed, not that 300 is the right target. Validating that requires comparing retrieval quality against other configs, which only becomes a meaningful comparison once hybrid search and reranking exist too (a bad number today could just as easily be masked or amplified by a weak retrieval method). Until then, changing this is a config edit, not a code change: it's a `ParentChildChunker` constructor behind a `Chunker` protocol, with `parent_tokens`/`child_tokens`/`overlap` read straight from `configs/*.yaml`.

Worth remembering why 300 isn't fully trustworthy even on its own terms: a `pysbd` sentence-segmentation bug (misreading one edition's dash typography) produced a single "sentence" over 1000 tokens, which blew one child to 1055 tokens before a hard-split safety net was added. The number is only as reliable as everything upstream of it — another edition could still surface a segmentation quirk the safety net doesn't fully compensate for.
