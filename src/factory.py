"""Reads a config and returns the configured implementation of each
interface. An experiment becomes: copy a config, change one line, run it.
"""

from pathlib import Path

import yaml

from chunking.parent_child import ParentChildChunker
from embedders.bge_m3 import BGEM3Embedder
from parsers.gutenberg import GutenbergParser
from parsers.standard_ebooks import StandardEbooksParser
from stores.pgvector_store import PgVectorStore

DSN = "postgresql://rag:rag@localhost:5432/books"

PARSERS = {"standard_ebooks": StandardEbooksParser, "gutenberg": GutenbergParser}
EMBEDDERS = {"bge-m3": BGEM3Embedder}
VECTOR_STORES = {"pgvector": PgVectorStore}


def load_config(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text())


def build_parser(config: dict):
    return PARSERS[config["parser"]]()


def build_chunker(config: dict):
    c = config["chunker"]
    if c["type"] != "parent_child":
        raise ValueError(f"unknown chunker type: {c['type']}")
    return ParentChildChunker(parent_tokens=c["parent_tokens"], child_tokens=c["child_tokens"], overlap=c["overlap"])


def build_embedder(config: dict):
    return EMBEDDERS[config["embedder"]]()


def build_vector_store(config: dict):
    return VECTOR_STORES[config["vector_store"]](DSN)


def chunk_config_name(config: dict) -> str:
    c = config["chunker"]
    return f"size{c['child_tokens']}_overlap{c['overlap']}"
