"""Run the eval with the HNSW index disabled (exact scan), book-filtered,
for the record alongside the normal filtered/unfiltered runs. See
eval/hnsw_vs_exact.py for the per-question comparison this corroborates.

Usage: python eval/eval_exact.py configs/baseline.yaml [eval/questions_v2.jsonl]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import factory  # noqa: E402
from eval import QUESTIONS_PATH, evaluate  # noqa: E402


def main(config_path: str, questions_path: str = QUESTIONS_PATH) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)
    store.conn.execute("SET enable_indexscan = off")
    store.conn.execute("SET enable_bitmapscan = off")

    questions = [json.loads(l) for l in Path(questions_path).read_text().splitlines() if l.strip()]
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    report = evaluate(embedder, store, questions, book_ids, filter_by_book=True)
    run_config = {
        "name": config["name"], "retrieval": "dense_exact", "embedding": config["embedder"],
        "chunk_config": factory.chunk_config_name(config), "book_filter": True, "questions": questions_path,
    }
    store.conn.execute("INSERT INTO eval_runs (config, metrics) VALUES (%s, %s)",
                        (json.dumps(run_config), json.dumps(report)))
    store.conn.commit()
    print(json.dumps(run_config), "\n", json.dumps(report, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else QUESTIONS_PATH)
