"""Run the eval set through the configured pipeline: recall@k (any evidence
piece found), full_recall@k (every piece found), and MRR — filtered and
unfiltered by book, saved to eval_runs. not_in_book questions have no
evidence so they're excluded (used later for generation testing).

Usage: python scripts/eval.py configs/baseline.yaml [eval/questions_v2.jsonl]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import factory  # noqa: E402
from stores.pgvector_store import fetch_chunks  # noqa: E402

QUESTIONS_PATH = "eval/questions_v2.jsonl"


def covers(chunk_meta: dict, ch: int, p: int, book_id: int) -> bool:
    return (chunk_meta["book_id"] == book_id and chunk_meta["chapter_num"] == ch
            and chunk_meta["paragraph_start"] <= p <= chunk_meta["paragraph_end"])


def piece_found(metas: list[dict], piece: list[list[int]], book_id: int) -> bool:
    return any(covers(m, ch, p, book_id) for m in metas for ch, p in piece)


def score_question(metas: list[dict], evidence: list[list[list[int]]], book_id: int,
                    k_values=(1, 5, 10, 20)) -> dict:
    scores = {}
    for k in k_values:
        top = metas[:k]
        found = [piece_found(top, piece, book_id) for piece in evidence]
        scores[f"recall@{k}"] = float(any(found)) if found else 0.0
        scores[f"full_recall@{k}"] = float(all(found)) if found else 0.0
    first = next((i + 1 for i, m in enumerate(metas)
                  if any(covers(m, ch, p, book_id) for piece in evidence for ch, p in piece)), None)
    scores["reciprocal_rank"] = 1 / first if first else 0.0
    return scores


def search(embedder, store, query: str, k: int, book_id: int | None = None):
    qvec = embedder.embed_query(query)
    hits = store.search(qvec, k=k, book_id=book_id)  # [(chunk_id, score), ...] — no text
    meta = fetch_chunks(store.conn, [cid for cid, _ in hits])  # text/metadata from Postgres
    return [meta[cid] for cid, _ in hits if cid in meta]


def evaluate(embedder, store, questions, book_ids, filter_by_book: bool, k_values=(1, 5, 10, 20)):
    per_type = defaultdict(list)
    for q in questions:
        if q["type"] == "not_in_book":
            continue
        book_id = book_ids[q["source_id"]]
        metas = search(embedder, store, q["question"], k=max(k_values),
                        book_id=book_id if filter_by_book else None)
        scores = score_question(metas, q["evidence"], book_id, k_values)
        per_type[q["type"]].append(scores)
        per_type["ALL"].append(scores)

    report = {}
    for qtype, rows in per_type.items():
        n = len(rows)
        agg = {key: round(sum(r[key] for r in rows) / n, 3) for key in rows[0]}
        agg["n"] = n
        report[qtype] = agg
    return report


def main(config_path: str, questions_path: str = QUESTIONS_PATH) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)

    questions = [json.loads(l) for l in Path(questions_path).read_text().splitlines() if l.strip()]
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    for filtered in (True, False):
        report = evaluate(embedder, store, questions, book_ids, filter_by_book=filtered)
        run_config = {
            "name": config["name"], "retrieval": config["retrieval"]["method"],
            "embedding": config["embedder"], "chunk_config": factory.chunk_config_name(config),
            "book_filter": filtered, "questions": questions_path,
        }
        store.conn.execute("INSERT INTO eval_runs (config, metrics) VALUES (%s, %s)",
                            (json.dumps(run_config), json.dumps(report)))
        print(json.dumps(run_config), "\n", json.dumps(report, indent=2))
    store.conn.commit()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else QUESTIONS_PATH)
