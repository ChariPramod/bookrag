"""Upload the audited eval questions as a Langfuse dataset and run the
baseline as a Langfuse experiment (filtered, unfiltered, and exact-scan),
recording recall@k, full_recall@k, and reciprocal_rank as per-question
scores. Needs LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST in
the environment (see .env.example).

Usage: python scripts/eval_langfuse.py configs/baseline.yaml
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import factory  # noqa: E402
from eval import QUESTIONS_PATH, score_question, search  # noqa: E402

DATASET_NAME = "book-rag-golden-v2"
K_VALUES = (1, 5, 10, 20)

# Our PgVectorStore holds one shared psycopg connection, not a pool —
# concurrent task execution would interleave queries on it.
MAX_CONCURRENCY = 1


def load_questions(questions_path: str) -> list[dict]:
    all_q = [json.loads(l) for l in Path(questions_path).read_text().splitlines() if l.strip()]
    return [q for q in all_q if q["type"] != "not_in_book"]  # no evidence to score against


def upload_dataset(client: Langfuse, questions: list[dict]) -> None:
    try:
        client.get_dataset(DATASET_NAME)
    except Exception:
        client.create_dataset(name=DATASET_NAME, description="book-rag retrieval eval v2: audited, evidence-piece scoring")

    # id=q["id"] makes this an upsert, so item content stays in sync when a
    # question's evidence is corrected later, not just on first upload.
    for q in questions:
        client.create_dataset_item(
            dataset_name=DATASET_NAME,
            id=q["id"],
            input=q,
            expected_output=q["evidence"],
            metadata={"type": q["type"], "id": q["id"], "source_id": q["source_id"]},
        )
    print(f"upserted {len(questions)} items to dataset {DATASET_NAME!r}")


def make_task(embedder, store, book_ids: dict, filter_by_book: bool):
    def task(*, item, **kwargs):
        q = item.input
        book_id = book_ids[q["source_id"]]
        metas = search(embedder, store, q["question"], k=max(K_VALUES),
                        book_id=book_id if filter_by_book else None)
        return score_question(metas, q["evidence"], book_id, K_VALUES)
    return task


def make_metric_evaluator(key: str):
    def evaluator(*, output, **kwargs):
        return {"name": key, "value": output[key]}
    return evaluator


def run_experiment(client, embedder, store, dataset, book_ids, run_name, filter_by_book):
    metric_keys = [f"recall@{k}" for k in K_VALUES] + [f"full_recall@{k}" for k in K_VALUES] + ["reciprocal_rank"]
    result = client.run_experiment(
        name=run_name,
        data=dataset.items,
        task=make_task(embedder, store, book_ids, filter_by_book),
        evaluators=[make_metric_evaluator(k) for k in metric_keys],
        max_concurrency=MAX_CONCURRENCY,
        metadata={"book_filter": filter_by_book},
    )
    print(f"{run_name}: {result.dataset_run_url}")


def main(config_path: str, questions_path: str = QUESTIONS_PATH) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)
    client = Langfuse()

    questions = load_questions(questions_path)
    upload_dataset(client, questions)
    dataset = client.get_dataset(DATASET_NAME)
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    run_experiment(client, embedder, store, dataset, book_ids,
                   f"{config['name']} filtered", filter_by_book=True)
    run_experiment(client, embedder, store, dataset, book_ids,
                   f"{config['name']} unfiltered", filter_by_book=False)

    store.conn.execute("SET enable_indexscan = off")
    store.conn.execute("SET enable_bitmapscan = off")
    run_experiment(client, embedder, store, dataset, book_ids,
                   f"{config['name']} exact-scan", filter_by_book=True)
    store.conn.execute("SET enable_indexscan = on")
    store.conn.execute("SET enable_bitmapscan = on")

    client.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else QUESTIONS_PATH)
