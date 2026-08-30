"""Read-only Chroma retrieve. Same MiniLM model as ingest."""

from __future__ import annotations

from allowlist import FUNDS
from embed_model import embed_texts
from store import get_collection

TOP_K = 5
WEAK_DISTANCE = 0.75


def _slug_for_url(url: str) -> str | None:
    for fund in FUNDS:
        if fund["url"] == url:
            return fund["slug"]
    return None


def _as_hits(raw) -> list[dict]:
    if not raw.get("ids"):
        return []
    ids = raw["ids"][0] if isinstance(raw["ids"][0], list) else raw["ids"]
    if not ids:
        return []
    docs = raw["documents"][0] if raw["documents"] and isinstance(raw["documents"][0], list) else raw["documents"]
    metas = raw["metadatas"][0] if raw["metadatas"] and isinstance(raw["metadatas"][0], list) else raw["metadatas"]
    dists = None
    if raw.get("distances"):
        dists = raw["distances"][0] if isinstance(raw["distances"][0], list) else raw["distances"]
    hits = []
    for i, chunk_id in enumerate(ids):
        if chunk_id is None:
            continue
        hits.append(
            {
                "chunk_id": chunk_id,
                "text": docs[i],
                "source_url": metas[i]["source_url"],
                "fund_label": metas[i]["fund_label"],
                "ingested_at": metas[i]["ingested_at"],
                "distance": float(dists[i]) if dists is not None else 0.0,
            }
        )
    return hits


def _facts_hit(collection, url: str) -> dict | None:
    slug = _slug_for_url(url)
    if not slug:
        return None
    raw = collection.get(ids=[f"{slug}-000"], include=["documents", "metadatas"])
    if not raw["ids"]:
        return None
    return {
        "chunk_id": raw["ids"][0],
        "text": raw["documents"][0],
        "source_url": raw["metadatas"][0]["source_url"],
        "fund_label": raw["metadatas"][0]["fund_label"],
        "ingested_at": raw["metadatas"][0]["ingested_at"],
        "distance": 0.0,
    }


def retrieve(question: str, primary_url: str | None = None) -> dict:
    collection = get_collection()
    query_vec = embed_texts([question])[0]

    kwargs = {
        "query_embeddings": [query_vec],
        "n_results": TOP_K,
        "include": ["documents", "metadatas", "distances"],
    }
    if primary_url:
        scoped = _as_hits(collection.query(**kwargs, where={"source_url": primary_url}))
        global_hits = _as_hits(collection.query(**kwargs))
        seen = {h["chunk_id"] for h in scoped}
        hits = scoped + [h for h in global_hits if h["chunk_id"] not in seen]
        facts = _facts_hit(collection, primary_url)
        if facts:
            hits = [facts] + [h for h in hits if h["chunk_id"] != facts["chunk_id"]]
        hits = hits[:TOP_K]
    else:
        hits = _as_hits(collection.query(**kwargs))
        facts = [h for h in hits if "Fund facts from this Groww page:" in h["text"]]
        rest = [h for h in hits if h not in facts]
        if facts:
            hits = facts + rest

    blob = " ".join(h["text"].lower() for h in hits)
    has_fact = any(
        key in blob
        for key in (
            "expense ratio",
            "exit load",
            "min sip",
            "min. for sip",
            "benchmark",
            "nfo risk",
            "plan type",
        )
    )
    best = hits[0]["distance"] if hits else 1.0
    weak = (not hits) or (best > WEAK_DISTANCE and not has_fact)
    citation = hits[0] if hits else None
    if primary_url and hits:
        citation = next((h for h in hits if h["source_url"] == primary_url), hits[0])
    return {"hits": hits, "weak": weak, "citation": citation}
