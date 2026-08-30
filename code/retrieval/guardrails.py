"""Pre-retrieval guardrails. Do not store PII."""

from __future__ import annotations

import re

from allowlist import FUNDS

DEFAULT_URL = FUNDS[0]["url"]
DEFAULT_LABEL = FUNDS[0]["fund_label"]

_PII = [
    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I),
    re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b"),
    re.compile(r"\b(pan|aadhaar|aadhar|otp|account number|phone number)\b", re.I),
]

_ADVICE = re.compile(
    r"\b(should i|buy|sell|switch|advise me|ignore (the )?rules|invest in this)\b",
    re.I,
)

_COMPARE = re.compile(
    r"\b(which (fund |of these )?(is |gave )?(the )?best|best return|compare (returns|funds)|highest return)\b",
    re.I,
)

_OTHER_AMC = re.compile(
    r"\b(sbi|icici|nippon|kotak|axis|uti|tata|motilal|quant|mirae|ppfas|parag parikh|dsp|franklin|invesco|bandhan)\b",
    re.I,
)

_OTHER_HDFC = re.compile(
    r"\bhdfc\b.+\b(mid cap|index|gilt|liquid|overnight|credit risk|corporate bond|nfo)\b",
    re.I,
)

_FUND_HINTS = [
    (FUNDS[0], ("large cap", "large-cap", "hdfc-large-cap-fund-direct-growth")),
    (FUNDS[1], ("flexi", "flexi cap", "equity-fund", "hdfc equity", "hdfc-equity-fund-direct-growth")),
    (FUNDS[2], ("elss", "tax saver", "hdfc-elss-tax-saver", "lock-in", "lock in")),
    (FUNDS[3], ("small cap", "small-cap", "hdfc-small-cap-fund-direct-growth")),
    (FUNDS[4], ("balanced advantage", "baf", "hdfc-balanced-advantage")),
]


def named_funds(question: str) -> list[dict]:
    q = question.lower()
    found = []
    for fund, hints in _FUND_HINTS:
        if any(h in q for h in hints) or fund["fund_label"].lower() in q:
            found.append(fund)
    return found


def cite_url(question: str) -> tuple[str, str]:
    named = named_funds(question)
    if named:
        return named[0]["url"], named[0]["fund_label"]
    return DEFAULT_URL, DEFAULT_LABEL


def _format(body: str, url: str, ingested_at: str) -> str:
    return f"{body.strip()}\n\nSource: {url}\nLast updated from sources: {ingested_at}"


_FAQ_FIELD = re.compile(
    r"\b(expense ratio|exit load|sip|lumpsum|lock-?in|riskometer|benchmark|category|plan type)\b",
    re.I,
)


def classify(question: str) -> dict | None:
    text = (question or "").strip()
    if not text or len(text) < 3 or not re.search(r"[a-zA-Z]", text):
        url, _ = cite_url(text)
        return {
            "kind": "refuse_empty",
            "body": "Please rephrase your question as a factual FAQ about one of the five HDFC funds on Groww.",
            "url": url,
        }
    if _FAQ_FIELD.search(text) and not named_funds(text) and "hdfc" not in text.lower():
        url, _ = cite_url(text)
        return {
            "kind": "refuse_empty",
            "body": "Please name one of the five funds: HDFC Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, or Balanced Advantage.",
            "url": url,
        }
    if any(p.search(text) for p in _PII):
        url, _ = cite_url(text)
        return {
            "kind": "refuse_pii",
            "body": "We never collect PII. Do not share PAN, Aadhaar, account numbers, OTPs, email, or phone. Rephrase without personal data.",
            "url": url,
        }
    if _COMPARE.search(text):
        url, _ = cite_url(text)
        return {
            "kind": "refuse_compare",
            "body": "This FAQ does not compute or compare returns. Open the cited Groww fund page for the official factsheet and returns section.",
            "url": url,
        }
    if _ADVICE.search(text):
        url, _ = cite_url(text)
        return {
            "kind": "refuse_advice",
            "body": "This is a facts-only FAQ and does not give buy, sell, or switch opinions.",
            "url": url,
        }
    if _OTHER_AMC.search(text) or _OTHER_HDFC.search(text):
        url, _ = cite_url(text)
        return {
            "kind": "refuse_corpus",
            "body": "We only cover five HDFC Direct Growth pages on Groww (Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage).",
            "url": url,
        }
    return None

