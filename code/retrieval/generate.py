"""Mistral generation from retrieved chunks only. Key from .env, never committed."""

from __future__ import annotations

import os

import requests

SYSTEM = """You are a facts-only FAQ assistant for five HDFC Direct Growth funds on Groww.
Use only the provided chunks. Prefer the "Fund facts from this Groww page" block.
Answer the asked field directly in at most 3 short sentences (for example: expense ratio, SIP minimum, exit load, benchmark, riskometer, plan type).
Do not invent numbers. Do not give investment advice. Do not say best, safe, or should.
Do not compare funds or compute returns.
Only say you do not have the fact if that field is truly absent from the chunks.
Do not add a source URL; the system will append one citation."""

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-small-latest"


def generate(question: str, hits: list[dict]) -> str:
    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not key:
        raise RuntimeError("MISTRAL_API_KEY missing. Put it in .env at the project root.")
    context = "\n\n---\n\n".join(h["text"] for h in hits)
    user = f"Question:\n{question}\n\nChunks:\n{context}"
    response = requests.post(
        MISTRAL_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "temperature": 0.1,
            "max_tokens": 220,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"].strip()
    return text
