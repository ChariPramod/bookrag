"""All Protocol definitions in one place, so factory.py has one thing to
read and every implementation has one contract to satisfy."""

from pathlib import Path
from typing import Any, Protocol


class BookParser(Protocol):
    def parse(self, path: Path, source_id: str) -> dict: ...


class Chunker(Protocol):
    """Turns a parsed book into parents (each with their children nested
    inside). Persisting them to Postgres is the caller's job, not the
    chunker's — chunking strategy and storage are separate concerns."""

    def chunk(self, book: dict) -> list[dict]: ...


class Embedder(Protocol):
    def embed(self, texts: list[str], batch_size: int = 32) -> Any: ...


class VectorStore(Protocol):
    """Holds only vectors and chunk IDs — never text. Chunk text and
    metadata always come from Postgres, looked up by the IDs this returns.
    That's what lets a Pinecone/Qdrant store slot in later without touching
    anything downstream of search()."""

    def upsert(self, rows: list[tuple[int, Any]]) -> None: ...

    def search(self, query_vector: Any, k: int, book_id: int | None = None) -> list[tuple[int, float]]: ...
