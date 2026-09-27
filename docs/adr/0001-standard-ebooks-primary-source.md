# Standard Ebooks is the primary book source; Gutenberg is the fallback

We built the ingest pipeline against Project Gutenberg plain text first, then rebuilt it against Standard Ebooks (EPUB) for the same three books and kept both. New books are sourced from Standard Ebooks when available; Gutenberg's `GutenbergParser` stays as the fallback for books Standard Ebooks doesn't carry, since its catalog is far smaller.

## Why

Gutenberg plain text has no machine-readable structure, so the parser had to *infer* it: a license-header regex, a hand-written chapter-heading regex per book, a table-of-contents false-match trap, and a line-unwrapping heuristic to recover paragraphs from ~70-char hard wraps. Each of these failed at least once in ways specific to plain-text inference, not to the books themselves: one edition's chapter 1 had no heading at all and silently merged into the front matter, requiring a special-cased recovery heuristic — which then over-fired on a different book's table of contents until scoped down; a sentence-segmentation library misread one edition's `.--` dash typography as a single 1000+-token "sentence," which cascaded into an oversized retrieval chunk; the recovered chapter 1 still has the book's preface glued to its front, accepted as a tradeoff rather than fixed.

Standard Ebooks ships EPUB, which is HTML with real semantic markup: `<body epub:type="frontmatter/backmatter/bodymatter">` marks structural sections directly, chapters are real heading tags, paragraphs are real `<p>` tags, italics are `<i>`/`<em>`. None of the four bugs above are possible by construction — they were all artifacts of guessing structure from plain-text formatting conventions. The EPUB parser ended up roughly half the code of the Gutenberg one (no header/footer regex, no per-book chapter regex, no ToC trap, no line-unwrapping). Standard Ebooks also publishes each book's word count, giving a verification check Gutenberg has no equivalent of; all three books landed within 1.3% of it (one within 0.01%).

The one new failure mode EPUB introduced: invisible Unicode typography characters (word joiners, zero-width no-break spaces, hair spaces) that Standard Ebooks uses for fine typesetting around dashes. One of them was missed on the first pass and found 748 times in a single book on inspection.

## Consequences

Both parsers implement one `BookParser` protocol (`parse(path, source_id) -> dict`) and return the identical JSON shape, so chunking, loading, embedding, and eval are unaffected by which parser produced the data — swapping sources only ever touches the ingest layer.
