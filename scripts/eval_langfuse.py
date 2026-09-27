"""Upload the eval questions as a Langfuse dataset and run the baseline as
a Langfuse experiment (filtered and unfiltered), recording recall@k and MRR
as per-question scores. Needs LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY /
LANGFUSE_HOST in the environment (see .env.example) — sign up for Langfuse
Cloud's Hobby tier and create a project first.

Usage: python scripts/eval_langfuse.py configs/baseline.yaml
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import factory  # noqa: E402
from eval import is_hit, search  # noqa: E402

DATASET_NAME = "book-rag-eval"
K_VALUES = (1, 5, 10, 20)

# Our PgVectorStore holds one shared psycopg connection, not a pool —
# concurrent task execution would interleave queries on it. Keep this at 1
# until the store is made connection-per-task or pooled.
MAX_CONCURRENCY = 1


def load_questions() -> list[dict]:
    all_q = [json.loads(l) for l in Path("eval/questions.jsonl").read_text().splitlines() if l.strip()]
    return [q for q in all_q if q["type"] != "not_in_book"]  # no gold passage to score against


def upload_dataset(client: Langfuse, questions: list[dict]) -> None:
    try:
        existing = client.get_dataset(DATASET_NAME)
        if len(existing.items) >= len(questions):
            print(f"dataset {DATASET_NAME!r} already has {len(existing.items)} items, skipping upload")
            return
    except Exception:
        pass

    client.create_dataset(name=DATASET_NAME, description="book-rag retrieval eval: 45 questions across 3 books")
    for q in questions:
        client.create_dataset_item(
            dataset_name=DATASET_NAME,
            input=q,
            expected_output=q["gold"],
            metadata={"type": q["type"], "id": q["id"], "source_id": q["source_id"]},
        )
    print(f"uploaded {len(questions)} items to dataset {DATASET_NAME!r}")


def make_task(embedder, store, book_ids: dict, filter_by_book: bool):
    def task(*, item, **kwargs):
        q = item.input
        book_id = book_ids[q["source_id"]]
        results = search(embedder, store, q["question"], k=max(K_VALUES),
                          book_id=book_id if filter_by_book else None)
        rank = next((i + 1 for i, (_, _, m) in enumerate(results) if is_hit(m, q["gold"], book_id)), None)
        return {"rank": rank}
    return task


def make_recall_evaluator(k: int):
    def evaluator(*, output, **kwargs):
        rank = output.get("rank")
        return {"name": f"recall@{k}", "value": 1 if rank is not None and rank <= k else 0}
    return evaluator


def reciprocal_rank_evaluator(*, output, **kwargs):
    rank = output.get("rank")
    return {"name": "reciprocal_rank", "value": 1 / rank if rank else 0}


def main(config_path: str) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)
    client = Langfuse()

    questions = load_questions()
    upload_dataset(client, questions)
    dataset = client.get_dataset(DATASET_NAME)

    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())
    evaluators = [make_recall_evaluator(k) for k in K_VALUES] + [reciprocal_rank_evaluator]

    for filtered in (True, False):
        result = client.run_experiment(
            name=f"{config['name']} (book_filter={filtered})",
            data=dataset.items,
            task=make_task(embedder, store, book_ids, filtered),
            evaluators=evaluators,
            max_concurrency=MAX_CONCURRENCY,
            metadata={
                "config": config["name"], "embedding": config["embedder"],
                "chunk_config": factory.chunk_config_name(config), "book_filter": filtered,
            },
        )
        print(f"book_filter={filtered}: {result.dataset_run_url}")

    client.flush()


if __name__ == "__main__":
    main(sys.argv[1])
