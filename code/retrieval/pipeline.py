"""Query pipeline: guardrails → retrieve → Mistral (or weak-retrieval refuse)."""

from __future__ import annotations

import re

import setup_paths  # noqa: F401

from guardrails import classify, named_funds, _format
from retrieve import retrieve
from generate import generate

_CAPITAL_GAINS = re.compile(r"capital\s*gains?.{0,40}(statement|download|how)", re.I)
_HOW_TO = re.compile(r"\b(download|statement|how to|steps?)\b", re.I)


def answer(question: str, generate_llm: bool = True) -> dict:
    ingested_at = "unknown"
    refused = classify(question)
    if refused:
        retrieved = retrieve(question)
        if retrieved["citation"] and refused["kind"] not in ("refuse_empty", "refuse_pii"):
            ingested_at = retrieved["citation"]["ingested_at"]
            refused["url"] = retrieved["citation"]["source_url"]
        elif retrieved["citation"]:
            ingested_at = retrieved["citation"]["ingested_at"]
        text = _format(refused["body"], refused["url"], ingested_at)
        return {
            "kind": refused["kind"],
            "text": text,
            "hits": retrieved["hits"],
            "weak": False,
        }

    named = named_funds(question)
    primary_url = named[0]["url"] if named else None
    retrieved = retrieve(question, primary_url=primary_url)
    hits = retrieved["hits"]
    citation = retrieved["citation"]
    ingested_at = citation["ingested_at"] if citation else "unknown"
    url = citation["source_url"] if citation else (primary_url or "")

    if _CAPITAL_GAINS.search(question):
        blob = " ".join(h["text"].lower() for h in hits)
        if not (_HOW_TO.search(blob) and "capital" in blob and "statement" in blob):
            body = "I don’t have that in the indexed pages. These five fund pages do not cover Groww account how-tos such as downloading a capital-gains statement."
            return {
                "kind": "not_in_corpus",
                "text": _format(body, url, ingested_at),
                "hits": hits,
                "weak": True,
            }

    context_hits = hits[:2]
    if retrieved["weak"]:
        body = "I don’t have that in the indexed pages."
        return {
            "kind": "weak",
            "text": _format(body, url, ingested_at),
            "hits": hits,
            "weak": True,
        }

    if not generate_llm:
        preview = hits[0]["text"][:400].replace("\n", " ")
        body = f"(retrieve-only) Top chunk: {preview}"
        return {
            "kind": "retrieve_only",
            "text": _format(body, url, ingested_at),
            "hits": hits,
            "weak": False,
        }

    body = generate(question, context_hits)
    return {
        "kind": "answer",
        "text": _format(body, url, ingested_at),
        "hits": hits,
        "weak": False,
    }
