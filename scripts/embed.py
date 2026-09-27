"""Embed every chunk for the config's chunk_config that isn't already
embedded. Safe to rerun: VectorStore.upsert skips chunks already present.

Usage: python scripts/embed.py configs/baseline.yaml
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import factory  # noqa: E402


def main(config_path: str) -> None:
    config = factory.load_config(config_path)
    embedder = factory.build_embedder(config)
    store = factory.build_vector_store(config)
    chunk_config = factory.chunk_config_name(config)

    rows = store.conn.execute(
        "SELECT id, embed_text FROM chunks WHERE chunk_config = %s ORDER BY id", (chunk_config,)
    ).fetchall()
    if not rows:
        print("nothing to embed")
        return

    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    print(f"embedding {len(texts)} chunks...")
    vecs = embedder.embed(texts, batch_size=32, show_progress_bar=True)
    store.upsert(list(zip(ids, vecs)))
    print("done")


if __name__ == "__main__":
    main(sys.argv[1])
