"""Print every question that misses full_recall@5 (not every evidence piece
found in the top 5), so misses can be read and sorted into causes by hand.

Usage: python eval/read_failures.py configs/baseline.yaml [eval/questions_v2.jsonl]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import factory  # noqa: E402
from eval import QUESTIONS_PATH, piece_found, search  # noqa: E402


def main(config_path: str, questions_path: str = QUESTIONS_PATH) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)

    questions = [json.loads(l) for l in Path(questions_path).read_text().splitlines() if l.strip()]
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    for q in questions:
        if q["type"] == "not_in_book":
            continue
        bid = book_ids[q["source_id"]]
        metas = search(embedder, store, q["question"], k=5, book_id=bid)
        found = [piece_found(metas, piece, bid) for piece in q["evidence"]]
        if not all(found):
            print(f"\nMISS [{q['type']}] {q['id']}: {q['question']}  "
                  f"pieces found: {sum(found)}/{len(found)}")
            for m in metas[:3]:
                print(f"   ch{m['chapter_num']} p{m['paragraph_start']}-{m['paragraph_end']}: {m['text'][:100]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/baseline.yaml",
         sys.argv[2] if len(sys.argv) > 2 else QUESTIONS_PATH)
