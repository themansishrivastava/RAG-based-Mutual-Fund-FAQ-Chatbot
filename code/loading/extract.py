"""Fetch public HTML for an allowlisted URL and extract page text. No other URLs."""

from __future__ import annotations

import json
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Fields from the same public page payload (not extra fetches).
FACT_KEYS = (
    "scheme_name",
    "fund_name",
    "fund_house",
    "amc",
    "category",
    "sub_category",
    "plan_type",
    "scheme_type",
    "expense_ratio",
    "exit_load",
    "min_sip_investment",
    "min_investment_amount",
    "mini_additional_investment",
    "benchmark",
    "benchmark_name",
    "nfo_risk",
    "description",
    "launch_date",
    "stamp_duty",
    "sip_allowed",
    "lumpsum_allowed",
    "nav",
    "nav_date",
)

DROP_TAGS = ("script", "style", "noscript", "svg", "nav", "footer", "header")


def fetch_html(url: str, timeout: int = 30) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def _visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(DROP_TAGS):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _next_data(html: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    node = soup.find("script", id="__NEXT_DATA__")
    if not node or not node.string:
        return None
    try:
        return json.loads(node.string)
    except json.JSONDecodeError:
        return None


def _facts_from_page_json(html: str) -> str:
    data = _next_data(html)
    if not data:
        return ""
    try:
        mf = data["props"]["pageProps"]["mfServerSideData"]
    except (KeyError, TypeError):
        return ""
    if not isinstance(mf, dict):
        return ""
    lines = ["Fund facts from this Groww page:"]
    for key in FACT_KEYS:
        if key not in mf:
            continue
        value = mf[key]
        if value is None or value == "":
            continue
        label = key.replace("_", " ")
        lines.append(f"{label}: {value}")
    return "\n".join(lines) if len(lines) > 1 else ""


def extract_raw_text(html: str) -> str:
    facts = _facts_from_page_json(html)
    visible = _visible_text(html)
    parts = [p for p in (facts, visible) if p]
    return "\n\n".join(parts)
