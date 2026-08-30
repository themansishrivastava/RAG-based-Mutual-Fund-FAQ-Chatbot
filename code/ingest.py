"""Run ingest phases in order. Used on Render build so Chroma exists (data/ is gitignored)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ROOT / "code" / "loading" / "run.py",
    ROOT / "code" / "chunking" / "run.py",
    ROOT / "code" / "embedding" / "run.py",
    ROOT / "code" / "vector_store" / "run.py",
]


def main() -> int:
    for script in STEPS:
        print(f"==> {script.relative_to(ROOT)}", flush=True)
        result = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
        if result.returncode != 0:
            return result.returncode
    print("Ingest complete.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
