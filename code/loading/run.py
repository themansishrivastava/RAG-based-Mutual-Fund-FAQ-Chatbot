"""Phase 1 — Data loading. Writes data/raw/ for the 5 allowlisted URLs only."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from allowlist import FUNDS
from extract import extract_raw_text, fetch_html

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"


def load_one(fund: dict, ingested_at: str) -> dict:
    url = fund["url"]
    html = fetch_html(url)
    raw_text = extract_raw_text(html)
    if not raw_text.strip():
        raise ValueError("empty extract")
    return {
        "url": url,
        "fund_label": fund["fund_label"],
        "category": fund["category"],
        "raw_text": raw_text,
        "ingested_at": ingested_at,
    }


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ingested_at = date.today().isoformat()
    ok: list[str] = []
    failed: list[dict] = []

    for fund in FUNDS:
        slug = fund["slug"]
        try:
            doc = load_one(fund, ingested_at)
            path = RAW_DIR / f"{slug}.json"
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            ok.append(slug)
            print(f"OK  {fund['fund_label']} -> {path.relative_to(ROOT)}")
        except Exception as exc:
            failed.append({"url": fund["url"], "fund_label": fund["fund_label"], "error": str(exc)})
            print(f"FAIL  {fund['fund_label']}: {exc}", file=sys.stderr)

    summary = {
        "ingested_at": ingested_at,
        "ok_count": len(ok),
        "ok": ok,
        "failed": failed,
        "note": "Fail closed: failed URLs were not substituted. Demo needs all 5.",
    }
    (RAW_DIR / "_ingest_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    if failed:
        print(f"Ingest incomplete: {len(ok)}/5 succeeded. See data/raw/_ingest_summary.json", file=sys.stderr)
        return 1
    print(f"Ingest complete: 5/5 pages. ingested_at={ingested_at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
