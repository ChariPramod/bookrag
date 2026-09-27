"""Run the eval set through the configured pipeline: recall@k and MRR,
filtered and unfiltered by book, saved to eval_runs. not_in_book questions
have no gold passage so they're excluded (used later for generation testing).

Usage: python scripts/eval.py configs/baseline.yaml
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import factory  # noqa: E402
from stores.pgvector_store import fetch_chunks  # noqa: E402


def is_hit(chunk_meta: dict, gold: list[list[int]], book_id: int) -> bool:
    return chunk_meta["book_id"] == book_id and any(
        chunk_meta["chapter_num"] == g_ch and chunk_meta["paragraph_start"] <= g_p <= chunk_meta["paragraph_end"]
        for g_ch, g_p in gold)


def search(embedder, store, query: str, k: int, book_id: int | None = None):
    qvec = embedder.embed_query(query)
    hits = store.search(qvec, k=k, book_id=book_id)  # [(chunk_id, score), ...] — no text
    meta = fetch_chunks(store.conn, [cid for cid, _ in hits])  # text/metadata from Postgres
    return [(cid, score, meta[cid]) for cid, score in hits if cid in meta]


def evaluate(embedder, store, questions, book_ids, filter_by_book: bool, k_values=(1, 5, 10, 20)):
    per_type = defaultdict(list)
    for q in questions:
        if q["type"] == "not_in_book":
            continue
        book_id = book_ids[q["source_id"]]
        results = search(embedder, store, q["question"], k=max(k_values),
                          book_id=book_id if filter_by_book else None)
        first_hit = next((i + 1 for i, (_, _, m) in enumerate(results) if is_hit(m, q["gold"], book_id)), None)
        per_type[q["type"]].append(first_hit)
        per_type["ALL"].append(first_hit)

    report = {}
    for qtype, ranks in per_type.items():
        report[qtype] = {f"recall@{k}": round(sum(1 for r in ranks if r and r <= k) / len(ranks), 3)
                          for k in k_values}
        report[qtype]["mrr"] = round(sum(1 / r for r in ranks if r) / len(ranks), 3)
        report[qtype]["n"] = len(ranks)
    return report


def main(config_path: str) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)

    questions = [json.loads(l) for l in Path("eval/questions.jsonl").read_text().splitlines() if l.strip()]
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    for filtered in (True, False):
        report = evaluate(embedder, store, questions, book_ids, filter_by_book=filtered)
        run_config = {
            "name": config["name"], "retrieval": config["retrieval"]["method"],
            "embedding": config["embedder"], "chunk_config": factory.chunk_config_name(config),
            "book_filter": filtered,
        }
        store.conn.execute("INSERT INTO eval_runs (config, metrics) VALUES (%s, %s)",
                            (json.dumps(run_config), json.dumps(report)))
        print(json.dumps(run_config), "\n", json.dumps(report, indent=2))
    store.conn.commit()


if __name__ == "__main__":
    main(sys.argv[1])
