"""Local ChromaDB: one collection, five allowlisted URLs only."""

from __future__ import annotations

from pathlib import Path

COLLECTION_NAME = "hdfc_groww_faq"
ROOT = Path(__file__).resolve().parents[2]
CHROMA_DIR = ROOT / "data" / "chroma"


def client():
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def rebuild_collection(ids, documents, embeddings, metadatas):
    """Replace the collection. Do not merge with a previous ingest."""
    chroma = client()
    existing = {c.name for c in chroma.list_collections()}
    if COLLECTION_NAME in existing:
        chroma.delete_collection(COLLECTION_NAME)
    collection = chroma.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return collection


def get_collection():
    """Read-only query path. Collection must already exist."""
    chroma = client()
    return chroma.get_collection(name=COLLECTION_NAME)
