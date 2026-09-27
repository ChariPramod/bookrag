CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS books (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    author      TEXT NOT NULL,
    source      TEXT NOT NULL,
    source_id   TEXT NOT NULL,
    raw_path    TEXT NOT NULL,
    UNIQUE (source, source_id)
);

CREATE TABLE IF NOT EXISTS parents (
    id             SERIAL PRIMARY KEY,
    book_id        INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_num    INT NOT NULL,
    chapter_title  TEXT NOT NULL,
    section_idx    INT NOT NULL,
    text           TEXT NOT NULL,
    token_count    INT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id               SERIAL PRIMARY KEY,
    parent_id        INT NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    book_id          INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_num      INT,
    chunk_idx        INT NOT NULL,
    paragraph_start  INT NOT NULL,
    paragraph_end    INT NOT NULL,
    text             TEXT NOT NULL,
    embed_text       TEXT,
    token_count      INT NOT NULL,
    chunk_config     TEXT NOT NULL,
    tsv              tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN (tsv);
CREATE INDEX IF NOT EXISTS chunks_book_idx ON chunks (book_id);
CREATE INDEX IF NOT EXISTS chunks_parent_idx ON chunks (parent_id);

CREATE TABLE IF NOT EXISTS emb_bge_m3 (
    chunk_id   INT PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    embedding  vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS emb_bge_m3_hnsw_idx ON emb_bge_m3
    USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS eval_runs (
    id          SERIAL PRIMARY KEY,
    config      JSONB NOT NULL,
    metrics     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
