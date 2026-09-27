"""Download, parse, chunk, and load books per a config. Safe to rerun: a
book already in the books table is skipped rather than reloaded.

Usage: python scripts/ingest.py configs/baseline.yaml
"""

import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import factory  # noqa: E402


def books_to_ingest(parser_name: str):
    """Yields (source, source_id, raw_path) for every configured book,
    downloading each first. The book list itself lives with its parser
    module, not as a fifth interface — there's only one list per source."""
    if parser_name == "standard_ebooks":
        from parsers.standard_ebooks import BOOKS, download_se
        for author, title in BOOKS:
            yield "standard_ebooks", f"{author}_{title}", download_se(author, title)
    elif parser_name == "gutenberg":
        from parsers.gutenberg import BOOKS, download
        for book_id in BOOKS:
            yield "gutenberg", str(book_id), download(book_id)
    else:
        raise ValueError(f"unknown parser: {parser_name}")


def already_loaded(conn, source: str, source_id: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM books WHERE source = %s AND source_id = %s", (source, source_id)
    ).fetchone() is not None


def load_book(conn, book: dict, parents: list[dict], raw_path: Path) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO books (title, author, source, source_id, raw_path) VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (book["title"], book["author"], book["source"], str(book["source_id"]), str(raw_path)))
        book_id = cur.fetchone()[0]

        for par in parents:
            cur.execute(
                """INSERT INTO parents (book_id, chapter_num, chapter_title, section_idx, text, token_count)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                (book_id, par["chapter_num"], par["chapter_title"], par["section_idx"],
                 par["text"], par["token_count"]))
            parent_id = cur.fetchone()[0]

            rows = [
                (parent_id, book_id, par["chapter_num"], cidx, c["para_start"], c["para_end"],
                 c["text"], c["embed_text"], c["token_count"], par["chunk_config"])
                for cidx, c in enumerate(par["children"])
            ]
            cur.executemany(
                """INSERT INTO chunks (parent_id, book_id, chapter_num, chunk_idx, paragraph_start,
                   paragraph_end, text, embed_text, token_count, chunk_config)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", rows)
    conn.commit()  # one transaction per book: a mid-book failure never leaves a half-loaded book


def main(config_path: str) -> None:
    config = factory.load_config(config_path)
    parser = factory.build_parser(config)
    chunker = factory.build_chunker(config)

    with psycopg.connect(factory.DSN) as conn:
        for source, source_id, raw_path in books_to_ingest(config["parser"]):
            if already_loaded(conn, source, source_id):
                print(f"skip (already loaded): {source_id}")
                continue
            book = parser.parse(raw_path, source_id)
            parents = chunker.chunk(book)
            load_book(conn, book, parents, raw_path)
            n_children = sum(len(p["children"]) for p in parents)
            print(f"loaded {book['title']}: {len(parents)} parents, {n_children} children")


if __name__ == "__main__":
    main(sys.argv[1])
