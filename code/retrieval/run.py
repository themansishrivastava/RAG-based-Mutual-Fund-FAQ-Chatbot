"""Backend retrieval CLI. No Streamlit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "retrieval"))

import setup_paths  # noqa: E402, F401

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from pipeline import answer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="HDFC Groww FAQ retrieval backend")
    parser.add_argument("question", nargs="?", default="", help="User question")
    parser.add_argument(
        "--chunks",
        action="store_true",
        help="Print retrieved chunks only; skip Mistral",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()
    question = args.question
    if not question and not sys.stdin.isatty():
        question = sys.stdin.read()

    result = answer(question, generate_llm=not args.chunks)
    if args.json:
        payload = {
            "kind": result["kind"],
            "text": result["text"],
            "weak": result["weak"],
            "hits": [
                {
                    "chunk_id": h["chunk_id"],
                    "distance": h["distance"],
                    "source_url": h["source_url"],
                    "fund_label": h["fund_label"],
                }
                for h in result["hits"]
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(result["text"])
    print("\n--- retrieved chunks ---")
    for h in result["hits"]:
        print(f"{h['chunk_id']}  dist={h['distance']:.4f}  {h['source_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
