"""BGE-M3 embedding model: one 1,024-dim vector per text, meaning-based.

BGE-M3 needs no instruction prefix on queries (some models do — check the
model card before reusing this pattern elsewhere). Always normalize, for
both chunks and queries, so cosine similarity behaves consistently.
"""

import torch
from langfuse import observe
from sentence_transformers import SentenceTransformer

DIM = 1024
MODEL_NAME = "BAAI/bge-m3"

_device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"


class BGEM3Embedder:
    def __init__(self):
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME, device=_device)
        return self._model

    def embed(self, texts: list[str], batch_size: int = 32, show_progress_bar: bool = False):
        """Bulk embedding, used by scripts/embed.py during ingestion.
        Deliberately not traced — tracing is for the query path."""
        return self.model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=show_progress_bar)

    @observe(name="embed_query")
    def embed_query(self, text: str):
        return self.embed([text])[0]
