"""Create hdfc_groww_faq if missing (Render often skips custom build commands)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "vector_store"))

from store import COLLECTION_NAME, client  # noqa: E402


def collection_ready() -> bool:
    try:
        chroma = client()
        names = {c.name for c in chroma.list_collections()}
        if COLLECTION_NAME not in names:
            return False
        return chroma.get_collection(COLLECTION_NAME).count() > 0
    except Exception:
        return False


def main() -> int:
    if collection_ready():
        print("Chroma collection ready.", flush=True)
        return 0
    print("Chroma missing; running ingest…", flush=True)
    return subprocess.call([sys.executable, str(ROOT / "code" / "ingest.py")], cwd=str(ROOT))


if __name__ == "__main__":
    sys.exit(main())
