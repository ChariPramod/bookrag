"""Compute the exact rank of every evidence piece for every question.
"Missed in the top 20" hides whether a passage was at rank 21 or rank 900 —
this doesn't. A NOT_CHUNKED row means a gold paragraph isn't covered by any
chunk: stop and fix that, it's a chunking or coverage bug, not a ranking one.

Usage: python eval/gold_ranks.py configs/baseline.yaml [eval/questions_v2.jsonl]
"""

import csv
import json
import sys
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import factory  # noqa: E402

QUESTIONS_PATH = "eval/questions_v2.jsonl"

SQL = """
WITH ranked AS (
  SELECT c.chapter_num, c.paragraph_start, c.paragraph_end,
         RANK() OVER (ORDER BY e.embedding <=> %(q)s) AS rnk
  FROM emb_bge_m3 e JOIN chunks c ON c.id = e.chunk_id
  WHERE c.book_id = %(book)s
)
SELECT MIN(rnk) FROM ranked
WHERE chapter_num = %(ch)s AND %(p)s BETWEEN paragraph_start AND paragraph_end
"""


def main(config_path: str, questions_path: str = QUESTIONS_PATH) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)

    questions = [json.loads(l) for l in Path(questions_path).read_text().splitlines() if l.strip()]

    with psycopg.connect(factory.DSN) as conn, open("eval/gold_ranks.csv", "w", newline="") as f:
        register_vector(conn)
        book_ids = dict(conn.execute("SELECT source_id, id FROM books").fetchall())
        total = dict(conn.execute("SELECT book_id, COUNT(*) FROM chunks GROUP BY book_id").fetchall())
        w = csv.writer(f)
        w.writerow(["id", "type", "piece", "best_rank", "chunks_in_book"])

        not_chunked = 0
        for q in questions:
            if q["type"] == "not_in_book":
                continue
            book = book_ids[q["source_id"]]
            qvec = embedder.embed_query(q["question"])
            for i, piece in enumerate(q["evidence"]):
                ranks = [conn.execute(SQL, {"q": qvec, "book": book, "ch": ch, "p": p}).fetchone()[0]
                         for ch, p in piece]
                ranks = [r for r in ranks if r is not None]
                if not ranks:
                    not_chunked += 1
                w.writerow([q["id"], q["type"], i, min(ranks) if ranks else "NOT_CHUNKED", total[book]])

    print(f"wrote eval/gold_ranks.csv ({not_chunked} NOT_CHUNKED rows)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else QUESTIONS_PATH)
