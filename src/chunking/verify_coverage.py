"""Confirm every paragraph in every parsed book is covered by at least one
chunk's [paragraph_start, paragraph_end] range. A gap is text that can never
be retrieved."""

import json
from pathlib import Path

import psycopg

PARSED = Path("data/parsed/standard_ebooks")
DSN = "postgresql://rag:rag@localhost:5432/books"


def main() -> None:
    gaps = 0
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for path in sorted(PARSED.glob("*.json")):
            book = json.loads(path.read_text())
            cur.execute(
                """SELECT c.chapter_num, c.paragraph_start, c.paragraph_end
                   FROM chunks c JOIN books b ON b.id = c.book_id
                   WHERE b.source = %s AND b.source_id = %s""",
                (book["source"], str(book["source_id"])))
            ranges_by_chapter = {}
            for chapter_num, start, end in cur.fetchall():
                ranges_by_chapter.setdefault(chapter_num, []).append((start, end))

            for ch in book["chapters"]:
                ranges = ranges_by_chapter.get(ch["num"], [])
                for i in range(len(ch["paragraphs"])):
                    if not any(start <= i <= end for start, end in ranges):
                        print(f"GAP: {book['title']} chapter {ch['num']} paragraph {i}")
                        gaps += 1

    if gaps == 0:
        print("coverage ok: every paragraph is covered by at least one chunk")
    else:
        print(f"{gaps} paragraph(s) not covered by any chunk")


if __name__ == "__main__":
    main()
