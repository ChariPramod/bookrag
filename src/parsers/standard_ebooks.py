"""Download and parse books from Standard Ebooks (EPUB). Primary source —
see docs/adr/0001-standard-ebooks-primary-source.md for why.

An EPUB is a zip of HTML files. Chapter structure is already marked up
(real headings, real <p> tags, <i> for italics), so parsing here is much
smaller than the Gutenberg plain-text pipeline: no header/footer markers,
no per-book chapter regex, no table-of-contents trap, no line unwrapping.
"""

import json
import re
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from ebooklib import epub

RAW = Path("data/raw/standard_ebooks")
PARSED = Path("data/parsed/standard_ebooks")

BOOKS = [
    ("joseph-conrad", "heart-of-darkness"),
    ("jane-austen", "pride-and-prejudice"),
    ("arthur-conan-doyle", "the-adventures-of-sherlock-holmes"),
]

SKIP_NAMES = ("titlepage", "imprint", "colophon", "uncopyright", "endnotes",
              "halftitlepage", "toc", "loi", "dedication", "epigraph")

# Word counts as listed on each book's Standard Ebooks page, for the
# verification check (a few % off is fine; a big gap means a skipped
# chapter or leaked front/back matter).
EXPECTED_WORD_COUNTS = {
    "joseph-conrad_heart-of-darkness": 38_496,
    "jane-austen_pride-and-prejudice": 121_970,
    "arthur-conan-doyle_the-adventures-of-sherlock-holmes": 104_582,
}

JUNK_MARKERS = ["<", ">", "&", "epub"]


def download_se(author: str, title: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    slug = f"{author}_{title}"
    out = RAW / f"{slug}.epub"
    if out.exists():
        return out
    # ?source=download is required: without it Standard Ebooks serves an
    # HTML "your download has started" interstitial instead of the file.
    url = f"https://standardebooks.org/ebooks/{author}/{title}/downloads/{slug}.epub?source=download"
    r = requests.get(url, headers={"User-Agent": "book-rag-learning/0.1 (your-email)"}, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)
    time.sleep(2)
    return out


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("⁠", "").replace("﻿", "")    # word joiner, zero-width no-break space
    text = text.replace(" ", " ").replace(" ", " ")  # no-break and hair spaces
    return re.sub(r"\s+", " ", text).strip()


def is_skipped(item, soup) -> bool:
    body_type = (soup.body.get("epub:type") or "") if soup.body else ""
    if "frontmatter" in body_type or "backmatter" in body_type:
        return True
    return any(name in item.get_name().lower() for name in SKIP_NAMES)


def parse_epub(path: Path, source_id: str) -> dict:
    book = epub.read_epub(str(path))
    title = book.get_metadata("DC", "title")[0][0]
    author = book.get_metadata("DC", "creator")[0][0]

    chapters = []
    for idref, _ in book.spine:
        item = book.get_item_with_id(idref)
        soup = BeautifulSoup(item.get_content(), "html.parser")
        if not soup.body or is_skipped(item, soup):
            continue

        # 1. Remove footnote reference links
        for a in soup.find_all("a", attrs={"epub:type": lambda v: v and "noteref" in v}):
            a.decompose()

        # 2. Grab the heading, then remove it so it isn't counted as a paragraph
        h = soup.body.find(["hgroup", "h1", "h2", "h3", "h4"])
        heading = clean(h.get_text(" ")) if h else ""
        for tag in soup.body.find_all(["header", "hgroup", "h1", "h2", "h3", "h4", "h5", "h6"]):
            tag.decompose()

        # 3. Collect paragraphs
        paragraphs = []
        for p in soup.body.find_all("p"):
            for br in p.find_all("br"):
                br.replace_with(" ")          # poetry line breaks become spaces
            text = clean(p.get_text())
            if text:
                paragraphs.append(text)

        if not paragraphs:                    # part and volume title pages
            continue
        chapters.append({"num": len(chapters) + 1,
                          "heading": heading or f"Section {len(chapters) + 1}",
                          "paragraphs": paragraphs})

    return {"source": "standard_ebooks", "source_id": source_id,
            "title": title, "author": author, "chapters": chapters}


class StandardEbooksParser:
    def parse(self, path: Path, source_id: str) -> dict:
        return parse_epub(path, source_id)


def report(book: dict) -> None:
    print(book["title"], "|", len(book["chapters"]), "chapters")
    for ch in book["chapters"]:
        words = sum(len(p.split()) for p in ch["paragraphs"])
        print(f"  {ch['num']:>3} {ch['heading'][:40]:<40} paras={len(ch['paragraphs']):>4} words={words:>6}")

    total_words = sum(len(p.split()) for ch in book["chapters"] for p in ch["paragraphs"])
    expected_words = EXPECTED_WORD_COUNTS.get(book["source_id"])
    note = f" (Standard Ebooks lists {expected_words:,})" if expected_words is not None else ""
    print(f"  total words: {total_words:,}{note}")

    text = "\n".join(p for ch in book["chapters"] for p in ch["paragraphs"])
    for marker in JUNK_MARKERS:
        count = text.count(marker)
        if count:
            print(f"  !! found {count} occurrence(s) of {marker!r} - HTML may have leaked through")

    first, last = book["chapters"][0], book["chapters"][-1]
    print(f"  first paragraph: {first['paragraphs'][0][:120]!r}")
    print(f"  last paragraph:  {last['paragraphs'][-1][:120]!r}")


def main() -> None:
    PARSED.mkdir(parents=True, exist_ok=True)
    parser = StandardEbooksParser()
    for author, title in BOOKS:
        path = download_se(author, title)
        source_id = f"{author}_{title}"
        book = parser.parse(path, source_id)
        (PARSED / f"{source_id}.json").write_text(json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8")
        report(book)
        print()


if __name__ == "__main__":
    main()
