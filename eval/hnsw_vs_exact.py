"""Compare HNSW (approximate) search against a forced exact scan, per
question, not just on average. Identical results mean HNSW loses nothing
at this corpus size. Differences mean raising hnsw.ef_search (starting at
100, then 200) until approximate matches exact.

Usage: python eval/hnsw_vs_exact.py configs/baseline.yaml [eval/questions_v2.jsonl]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import factory  # noqa: E402
from eval import QUESTIONS_PATH, piece_found, search  # noqa: E402


def first_hit_rank(metas, evidence, book_id) -> int | None:
    for i in range(1, len(metas) + 1):
        if all(piece_found(metas[:i], piece, book_id) for piece in evidence):
            return i
    return None


def main(config_path: str, questions_path: str = QUESTIONS_PATH) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)

    questions = [json.loads(l) for l in Path(questions_path).read_text().splitlines() if l.strip()]
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    diffs = []
    for q in questions:
        if q["type"] == "not_in_book":
            continue
        bid = book_ids[q["source_id"]]

        approx = search(embedder, store, q["question"], k=20, book_id=bid)
        approx_ids = [(m["chapter_num"], m["paragraph_start"], m["paragraph_end"]) for m in approx]

        store.conn.execute("SET enable_indexscan = off")
        store.conn.execute("SET enable_bitmapscan = off")
        exact = search(embedder, store, q["question"], k=20, book_id=bid)
        exact_ids = [(m["chapter_num"], m["paragraph_start"], m["paragraph_end"]) for m in exact]
        store.conn.execute("SET enable_indexscan = on")
        store.conn.execute("SET enable_bitmapscan = on")

        if approx_ids != exact_ids:
            approx_rank = first_hit_rank(approx, q["evidence"], bid)
            exact_rank = first_hit_rank(exact, q["evidence"], bid)
            diffs.append((q["id"], approx_rank, exact_rank))

    if not diffs:
        print(f"identical top-20 results for all {len(questions) - sum(1 for q in questions if q['type'] == 'not_in_book')} scored questions: HNSW loses nothing at this corpus size")
    else:
        print(f"{len(diffs)} question(s) differ between approximate and exact search:")
        print(f"{'id':10} {'approx_rank':12} {'exact_rank':10}")
        for qid, ar, er in diffs:
            print(f"{qid:10} {str(ar):12} {str(er):10}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/baseline.yaml",
         sys.argv[2] if len(sys.argv) > 2 else QUESTIONS_PATH)
