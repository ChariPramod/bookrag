"""Print every question that missed in the top 20 (book-filtered dense
search), so misses can be read and sorted into causes by hand.

Usage: python eval/read_failures.py configs/baseline.yaml
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import factory  # noqa: E402
from eval import is_hit, search  # noqa: E402


def main(config_path: str) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)

    questions = [json.loads(l) for l in Path("eval/questions.jsonl").read_text().splitlines() if l.strip()]
    book_ids = dict(store.conn.execute("SELECT source_id, id FROM books").fetchall())

    for q in questions:
        if q["type"] == "not_in_book":
            continue
        bid = book_ids[q["source_id"]]
        results = search(embedder, store, q["question"], k=20, book_id=bid)
        if not any(is_hit(m, q["gold"], bid) for _, _, m in results):
            print(f"\nMISS [{q['type']}] {q['id']}: {q['question']}  gold={q['gold']}")
            for _, score, m in results[:3]:
                print(f"   {score:.3f} ch{m['chapter_num']} p{m['paragraph_start']}-{m['paragraph_end']}: "
                      f"{m['text'][:100]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/baseline.yaml")
