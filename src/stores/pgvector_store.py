"""pgvector-backed VectorStore. search() returns only (chunk_id, score) —
never text. That's the contract every VectorStore implementation must keep:
swapping in Pinecone or Qdrant later should never require touching how
callers hydrate results, because they always go back to Postgres for that.
"""

from typing import Any

import psycopg
from langfuse import observe
from pgvector.psycopg import register_vector


class PgVectorStore:
    def __init__(self, dsn: str, table: str = "emb_bge_m3"):
        self.dsn = dsn
        self.table = table
        self._conn: psycopg.Connection | None = None

    @property
    def conn(self) -> psycopg.Connection:
        if self._conn is None:
            self._conn = psycopg.connect(self.dsn)
            register_vector(self._conn)
            # The HNSW index is approximate and explores ~40 candidates by
            # default; without this, a book_id filter can throw most of
            # them away and silently return fewer than k rows.
            self._conn.execute("SET hnsw.iterative_scan = relaxed_order")
            self._conn.execute("SET hnsw.ef_search = 100")
        return self._conn

    def upsert(self, rows: list[tuple[int, Any]]) -> None:
        with self.conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {self.table} (chunk_id, embedding) VALUES (%s, %s) "
                "ON CONFLICT (chunk_id) DO NOTHING",
                rows)
        self.conn.commit()

    @observe(name="vector_search")
    def search(self, query_vector: Any, k: int, book_id: int | None = None) -> list[tuple[int, float]]:
        sql = f"""
            SELECT e.chunk_id, 1 - (e.embedding <=> %(q)s) AS score
            FROM {self.table} e JOIN chunks c ON c.id = e.chunk_id
            WHERE (%(book)s::int IS NULL OR c.book_id = %(book)s)
            ORDER BY e.embedding <=> %(q)s
            LIMIT %(k)s
        """
        return self.conn.execute(sql, {"q": query_vector, "book": book_id, "k": k}).fetchall()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


@observe(name="fetch_chunks")
def fetch_chunks(conn: psycopg.Connection, chunk_ids: list[int]) -> dict[int, dict]:
    """Chunk text and metadata always come from Postgres, keyed by the IDs
    a VectorStore.search() call returned."""
    if not chunk_ids:
        return {}
    rows = conn.execute(
        """SELECT id, book_id, chapter_num, paragraph_start, paragraph_end, text
           FROM chunks WHERE id = ANY(%s)""",
        (chunk_ids,)
    ).fetchall()
    return {
        r[0]: {"book_id": r[1], "chapter_num": r[2], "paragraph_start": r[3], "paragraph_end": r[4], "text": r[5]}
        for r in rows
    }
