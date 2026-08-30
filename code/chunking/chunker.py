"""Small overlapping chunks. Fund name + fact fields stay in the same chunk. No cross-URL merge."""

from __future__ import annotations

CHUNK_SIZE = 700
OVERLAP = 150


def _prefix(fund_label: str) -> str:
    return f"Fund: {fund_label}\n"


def _windows(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    step = size - overlap
    if step < 1:
        step = size
    out: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end].strip()
        if piece:
            out.append(piece)
        if end >= len(text):
            break
        start += step
    return out


def split_facts_and_body(raw_text: str) -> tuple[str, str]:
    """Keep the structured facts block intact; window the rest of the page."""
    marker = "Fund facts from this Groww page:"
    if not raw_text.startswith(marker):
        return "", raw_text
    facts, _, rest = raw_text.partition("\n\n")
    return facts.strip(), rest.strip()


def chunk_document(doc: dict) -> list[dict]:
    fund_label = doc["fund_label"]
    source_url = doc["url"]
    ingested_at = doc["ingested_at"]
    prefix = _prefix(fund_label)

    facts, body = split_facts_and_body(doc["raw_text"])
    pieces: list[str] = []
    if facts:
        pieces.append(facts)
    pieces.extend(_windows(body, CHUNK_SIZE, OVERLAP))

    chunks: list[dict] = []
    slug = source_url.rstrip("/").rsplit("/", 1)[-1]
    for i, piece in enumerate(pieces):
        chunks.append(
            {
                "chunk_id": f"{slug}-{i:03d}",
                "text": prefix + piece,
                "source_url": source_url,
                "fund_label": fund_label,
                "ingested_at": ingested_at,
            }
        )
    return chunks
