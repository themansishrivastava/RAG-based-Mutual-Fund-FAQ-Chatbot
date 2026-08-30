"""Phase 4 — Vector store. Loads data/embeddings/vectors.json into local ChromaDB."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "loading"))
sys.path.insert(0, str(ROOT / "code" / "vector_store"))

from allowlist import ALLOWED_URLS  # noqa: E402
from store import CHROMA_DIR, COLLECTION_NAME, rebuild_collection  # noqa: E402

VECTORS_PATH = ROOT / "data" / "embeddings" / "vectors.json"


def load_records() -> list[dict]:
    if not VECTORS_PATH.exists():
        raise FileNotFoundError(f"missing {VECTORS_PATH.relative_to(ROOT)} — run embedding first")
    records = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    if not records:
        raise ValueError("no vectors to store")
    urls = set()
    for rec in records:
        url = rec.get("source_url")
        if url not in ALLOWED_URLS:
            raise ValueError(f"url not in allowlist: {url}")
        urls.add(url)
        if not rec.get("chunk_id") or not rec.get("text") or not rec.get("embedding"):
            raise ValueError(f"incomplete record: {rec.get('chunk_id')}")
    if urls != ALLOWED_URLS:
        missing = ALLOWED_URLS - urls
        raise ValueError(f"corpus incomplete; missing URLs: {sorted(missing)}")
    return records


def main() -> int:
    try:
        records = load_records()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1

    ids = [r["chunk_id"] for r in records]
    if len(ids) != len(set(ids)):
        print("FAIL  duplicate chunk_id", file=sys.stderr)
        return 1

    documents = [r["text"] for r in records]
    embeddings = [r["embedding"] for r in records]
    metadatas = [
        {
            "source_url": r["source_url"],
            "fund_label": r["fund_label"],
            "ingested_at": r["ingested_at"],
        }
        for r in records
    ]

    collection = rebuild_collection(ids, documents, embeddings, metadatas)
    count = collection.count()
    print(
        f"OK  collection={COLLECTION_NAME} count={count} "
        f"persist={CHROMA_DIR.relative_to(ROOT)}"
    )
    return 0 if count == len(records) else 1


if __name__ == "__main__":
    sys.exit(main())
