"""Phase 2 — Chunking. Reads data/raw/, writes data/chunks/. One URL per document; no merge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "loading"))

from allowlist import ALLOWED_URLS, FUNDS  # noqa: E402
from chunker import chunk_document  # noqa: E402

RAW_DIR = ROOT / "data" / "raw"
CHUNK_DIR = ROOT / "data" / "chunks"


def load_raw_docs() -> list[dict]:
    docs = []
    for fund in FUNDS:
        path = RAW_DIR / f"{fund['slug']}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing raw file: {path.relative_to(ROOT)} — run data loading first")
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("url") not in ALLOWED_URLS:
            raise ValueError(f"url not in allowlist: {doc.get('url')}")
        if doc.get("url") != fund["url"]:
            raise ValueError(f"url mismatch for {fund['slug']}")
        docs.append((fund["slug"], doc))
    return docs


def main() -> int:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    try:
        docs = load_raw_docs()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1

    all_chunks: list[dict] = []
    for slug, doc in docs:
        chunks = chunk_document(doc)
        if not chunks:
            print(f"FAIL  no chunks for {slug}", file=sys.stderr)
            return 1
        urls = {c["source_url"] for c in chunks}
        if urls != {doc["url"]}:
            print(f"FAIL  mixed URLs in {slug}", file=sys.stderr)
            return 1
        out = CHUNK_DIR / f"{slug}.json"
        out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        all_chunks.extend(chunks)
        print(f"OK  {doc['fund_label']}: {len(chunks)} chunks -> {out.relative_to(ROOT)}")

    index_path = CHUNK_DIR / "all.json"
    index_path.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_chunks)} chunks from 5 pages -> {index_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
