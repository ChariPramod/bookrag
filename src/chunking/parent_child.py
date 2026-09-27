"""Turn a parsed book (chapters of paragraphs) into parent/child chunks.

Parents are readable context windows (whole paragraphs, chapter-bounded).
Children are what gets embedded and searched: whole paragraphs when they
fit the budget, sentences when a paragraph doesn't, packed with overlap.
Children never cross their parent's boundary.
"""

import pysbd
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
_SEGMENTER = pysbd.Segmenter(language="en", clean=False)


def ntok(s: str) -> int:
    return len(ENC.encode(s))


def sentences(p: str) -> list[str]:
    return [s.strip() for s in _SEGMENTER.segment(p) if s.strip()]


def build_parents(chapter: dict, max_tokens: int) -> list[dict]:
    parents, cur, cur_tok, start = [], [], 0, 0
    for i, p in enumerate(chapter["paragraphs"]):
        t = ntok(p)
        if cur and cur_tok + t > max_tokens:
            parents.append({"para_start": start, "para_end": i - 1, "paras": cur})
            cur, cur_tok, start = [], 0, i
        cur.append(p)
        cur_tok += t
    if cur:
        parents.append({"para_start": start, "para_end": start + len(cur) - 1, "paras": cur})
    return parents


def hard_split(text: str, max_tokens: int) -> list[str]:
    """Last-resort split for a pysbd 'sentence' that's still oversized: usually
    a mis-segmentation caused by an edition's unusual punctuation (e.g. ".--"
    with no space, which pysbd doesn't recognize as a sentence boundary)."""
    ids = ENC.encode(text)
    return [ENC.decode(ids[i:i + max_tokens]) for i in range(0, len(ids), max_tokens)]


def units_for(parent: dict, max_child: int) -> list[tuple[int, str]]:
    units = []
    for offset, p in enumerate(parent["paras"]):
        idx = parent["para_start"] + offset
        if ntok(p) <= max_child:
            units.append((idx, p))
            continue
        for s in sentences(p):
            if ntok(s) <= max_child:
                units.append((idx, s))
            else:
                units.extend((idx, piece) for piece in hard_split(s, max_child))
    return units


def build_children(parent: dict, max_child: int, overlap: int) -> list[dict]:
    units = units_for(parent, max_child)
    children, cur = [], []
    for u in units:
        if cur and sum(ntok(t) for _, t in cur) + ntok(u[1]) > max_child:
            children.append(cur)
            tail, tail_tok = [], 0                  # carry overlap forward
            for x in reversed(cur):
                if tail_tok + ntok(x[1]) > overlap:
                    break
                tail.insert(0, x)
                tail_tok += ntok(x[1])
            cur = tail
        cur.append(u)
    if cur:
        children.append(cur)

    out = []
    for c in children:
        # Join units from the same paragraph with a space; a child that
        # spans a paragraph break gets "\n\n" so the break isn't lost.
        parts, prev_idx = [], None
        for idx, t in c:
            if prev_idx is not None and idx != prev_idx:
                parts.append("\n\n")
            elif prev_idx is not None:
                parts.append(" ")
            parts.append(t)
            prev_idx = idx
        out.append({
            "text": "".join(parts),
            "para_start": c[0][0],
            "para_end": c[-1][0],
        })
    return out


def embed_text(book: dict, chapter_heading: str, child_text: str) -> str:
    return f"{book['title']}, {chapter_heading}: {child_text}"


class ParentChildChunker:
    def __init__(self, parent_tokens: int = 2000, child_tokens: int = 300, overlap: int = 40,
                 config_name: str | None = None):
        self.parent_tokens = parent_tokens
        self.child_tokens = child_tokens
        self.overlap = overlap
        self.config_name = config_name or f"size{child_tokens}_overlap{overlap}"

    def chunk(self, book: dict) -> list[dict]:
        parents_out = []
        for ch in book["chapters"]:
            for sidx, par in enumerate(build_parents(ch, max_tokens=self.parent_tokens)):
                ptext = "\n\n".join(par["paras"])
                children = [
                    {
                        "text": c["text"],
                        "embed_text": embed_text(book, ch["heading"], c["text"]),
                        "para_start": c["para_start"],
                        "para_end": c["para_end"],
                        "token_count": ntok(c["text"]),
                    }
                    for c in build_children(par, max_child=self.child_tokens, overlap=self.overlap)
                ]
                parents_out.append({
                    "chapter_num": ch["num"],
                    "chapter_title": ch["heading"],
                    "section_idx": sidx,
                    "text": ptext,
                    "token_count": ntok(ptext),
                    "chunk_config": self.config_name,
                    "children": children,
                })
        return parents_out
