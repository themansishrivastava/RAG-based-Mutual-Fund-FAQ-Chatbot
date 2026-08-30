"""Phase 3 — Embedding. Reads data/chunks/all.json, writes data/embeddings/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "loading"))
sys.path.insert(0, str(ROOT / "code" / "embedding"))

from allowlist import ALLOWED_URLS  # noqa: E402
from model import MODEL_NAME, embed_texts  # noqa: E402

CHUNK_PATH = ROOT / "data" / "chunks" / "all.json"
OUT_DIR = ROOT / "data" / "embeddings"


def load_chunks() -> list[dict]:
    if not CHUNK_PATH.exists():
        raise FileNotFoundError(f"missing {CHUNK_PATH.relative_to(ROOT)} — run chunking first")
    chunks = json.loads(CHUNK_PATH.read_text(encoding="utf-8"))
    if not chunks:
        raise ValueError("no chunks to embed")
    for chunk in chunks:
        if chunk.get("source_url") not in ALLOWED_URLS:
            raise ValueError(f"url not in allowlist: {chunk.get('source_url')}")
        if not chunk.get("text", "").strip():
            raise ValueError(f"empty text: {chunk.get('chunk_id')}")
    return chunks


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        chunks = load_chunks()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks with {MODEL_NAME} (local)")
    vectors = embed_texts(texts, show_progress_bar=True)
    dim = len(vectors[0])

    records = []
    for chunk, vector in zip(chunks, vectors):
        records.append(
            {
                "chunk_id": chunk["chunk_id"],
                "embedding": vector,
                "text": chunk["text"],
                "source_url": chunk["source_url"],
                "fund_label": chunk["fund_label"],
                "ingested_at": chunk["ingested_at"],
            }
        )

    out_path = OUT_DIR / "vectors.json"
    out_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    meta = {
        "model": MODEL_NAME,
        "count": len(records),
        "dim": dim,
        "source": str(CHUNK_PATH.relative_to(ROOT)),
        "note": "Embedded chunk text only. Same model must be used at query time.",
    }
    (OUT_DIR / "_embed_summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"OK  {len(records)} vectors dim={dim} -> {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
