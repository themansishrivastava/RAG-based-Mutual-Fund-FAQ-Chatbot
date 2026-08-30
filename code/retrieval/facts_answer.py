"""Pull FAQ fields from the facts chunk without calling the LLM."""

from __future__ import annotations

import re


def _value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def from_facts(question: str, hits: list[dict]) -> str | None:
    if not hits:
        return None
    text = hits[0]["text"]
    label = hits[0]["fund_label"]
    q = question.lower()

    if "expense" in q:
        v = _value(text, "expense ratio")
        if v:
            return f"The expense ratio of {label} is {v}."
    if re.search(r"\bsip\b", q):
        v = _value(text, "min sip investment")
        if v:
            return f"The minimum SIP for {label} is ₹{v}."
    if "exit load" in q:
        v = _value(text, "exit load")
        if v:
            return f"The exit load of {label} is {v}."
    if "benchmark" in q:
        v = _value(text, "benchmark name") or _value(text, "benchmark")
        if v:
            return f"The benchmark of {label} is {v}."
    if "risk" in q or "riskometer" in q:
        v = _value(text, "nfo risk")
        if v:
            return f"The riskometer / risk level of {label} is {v}."
    if "lock" in q:
        return None
    if "lumpsum" in q or "lump sum" in q:
        v = _value(text, "min investment amount")
        if v:
            return f"The minimum lumpsum for {label} is ₹{v}."
    return None
