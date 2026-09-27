"""Download raw books from Project Gutenberg and parse them into data/parsed.

Only fetches a handful of books this way — Gutenberg blocks automated
crawling. For hundreds of books, use the PG-19 dataset on Hugging Face
instead.
"""

import json
import re
import time
import unicodedata
from pathlib import Path

import requests

RAW = Path("data/raw/gutenberg")
PARSED = Path("data/parsed/gutenberg")

BOOKS = {
    219: ("Heart of Darkness", "Joseph Conrad"),
    1342: ("Pride and Prejudice", "Jane Austen"),
    1661: ("The Adventures of Sherlock Holmes", "Arthur Conan Doyle"),
}
BOOK_IDS = list(BOOKS)

START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK", re.I)

# Chapter heading patterns are different for every book — inspect the file
# by hand and add an entry here before ingesting a new one.
HEADING_PATTERNS = {
    219: re.compile(r"^\s*(I|II|III)\s*$", re.M),
    1342: re.compile(r"^\s*CHAPTER\s+([IVXLC]+)\.?\s*$", re.M | re.I),
    1661: re.compile(r"^\s*(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\.\s+([A-Z][A-Z\s\-'’]+)$", re.M),
}

# Known chapter/story counts and rough word counts, used only to sanity-check the parse.
EXPECTED_CHAPTER_COUNTS = {219: 3, 1342: 61, 1661: 12}
EXPECTED_WORD_COUNTS = {219: 38_000, 1342: 120_000}

# Editions where chapter I's text starts right after the front matter with no
# heading of its own (the first heading found is "CHAPTER II."). Everything
# else treats a long stretch of leading text as front matter and drops it.
IMPLICIT_FIRST_CHAPTER = {1342}

JUNK_MARKERS = ["_", "[", "***", "Gutenberg"]


def download(book_id: int) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{book_id}.txt"
    if out.exists():  # never re-download
        return out
    url = f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8"
    r = requests.get(url, headers={"User-Agent": "book-rag-learning/0.1 (your-email)"}, timeout=30)
    r.raise_for_status()
    out.write_bytes(r.content)  # save bytes exactly as received
    time.sleep(2)  # be polite
    return out


def strip_gutenberg(text: str) -> str:
    text = text.replace("﻿", "")  # byte order mark
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    s, e = START.search(text), END.search(text)
    if not s or not e:
        raise ValueError("Gutenberg markers not found, inspect this file by hand")
    return text[s.end():e.start()].strip()


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\[Illustration[^\]]*\]", "", text, flags=re.S)   # illustration markers
    text = re.sub(r"\[\d+\]", "", text)                              # footnote markers
    text = re.sub(r"_([^_]+)_", r"\1", text)                          # _italics_ to plain
    text = re.sub(r"[ \t]+", " ", text)                               # collapse spaces
    return text.strip()


def split_chapters(body: str, pattern: re.Pattern, capture_leading: bool = False) -> list[dict]:
    matches = list(pattern.finditer(body))
    chapters = []

    if capture_leading and matches:
        leading = body[:matches[0].start()].strip()
        if len(leading) >= 500:
            chapters.append({"heading": "I", "text": leading})

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        if len(text) < 500:  # skips table-of-contents entries
            continue
        chapters.append({"heading": m.group(0).strip(), "text": text})
    return chapters


def to_paragraphs(chapter_text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", chapter_text)          # blank lines separate paragraphs
    paras = []
    for b in blocks:
        p = " ".join(line.strip() for line in b.splitlines())   # unwrap hard line breaks
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            paras.append(p)
    return paras


def process(book_id: int, title: str, author: str) -> dict:
    raw = (RAW / f"{book_id}.txt").read_text(encoding="utf-8")
    body = strip_gutenberg(raw)
    chapters = split_chapters(body, HEADING_PATTERNS[book_id], capture_leading=book_id in IMPLICIT_FIRST_CHAPTER)

    out = {"source": "gutenberg", "source_id": book_id, "title": title, "author": author, "chapters": []}
    for num, ch in enumerate(chapters, start=1):
        paras = to_paragraphs(clean_text(ch["text"]))
        out["chapters"].append({"num": num, "heading": ch["heading"], "paragraphs": paras})

    PARSED.mkdir(parents=True, exist_ok=True)
    (PARSED / f"{book_id}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


class GutenbergParser:
    """Fallback parser for books Standard Ebooks doesn't have. See
    docs/adr/0001-standard-ebooks-primary-source.md."""

    def parse(self, path: Path, source_id: str) -> dict:
        book_id = int(source_id)
        title, author = BOOKS[book_id]
        raw = path.read_text(encoding="utf-8")
        body = strip_gutenberg(raw)
        chapters = split_chapters(body, HEADING_PATTERNS[book_id], capture_leading=book_id in IMPLICIT_FIRST_CHAPTER)

        out = {"source": "gutenberg", "source_id": source_id, "title": title, "author": author, "chapters": []}
        for num, ch in enumerate(chapters, start=1):
            paras = to_paragraphs(clean_text(ch["text"]))
            out["chapters"].append({"num": num, "heading": ch["heading"], "paragraphs": paras})
        return out


def report(book: dict) -> None:
    print(book["title"], "|", len(book["chapters"]), "chapters")
    for ch in book["chapters"]:
        words = sum(len(p.split()) for p in ch["paragraphs"])
        print(f"  {ch['num']:>3} {ch['heading'][:40]:<40} paras={len(ch['paragraphs']):>4} words={words:>6}")

    expected_chapters = EXPECTED_CHAPTER_COUNTS.get(book["source_id"])
    if expected_chapters is not None and len(book["chapters"]) != expected_chapters:
        print(f"  !! expected {expected_chapters} chapters, got {len(book['chapters'])}")

    total_words = sum(len(p.split()) for ch in book["chapters"] for p in ch["paragraphs"])
    expected_words = EXPECTED_WORD_COUNTS.get(book["source_id"])
    note = f" (expected roughly {expected_words:,})" if expected_words is not None else ""
    print(f"  total words: {total_words:,}{note}")

    text = "\n".join(p for ch in book["chapters"] for p in ch["paragraphs"])
    for marker in JUNK_MARKERS:
        count = text.count(marker)
        if count:
            print(f"  !! found {count} occurrence(s) of {marker!r} - inspect for leftover junk")

    first, last = book["chapters"][0], book["chapters"][-1]
    print(f"  first paragraph: {first['paragraphs'][0][:120]!r}")
    print(f"  last paragraph:  {last['paragraphs'][-1][:120]!r}")


def main() -> None:
    for bid in BOOK_IDS:
        download(bid)

    for bid in BOOK_IDS:
        title, author = BOOKS[bid]
        book = process(bid, title, author)
        report(book)
        print()


if __name__ == "__main__":
    main()
