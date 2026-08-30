"""Put ingest modules on sys.path and alias embedding.model as embed_model."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for rel in ("code/loading", "code/vector_store", "code/embedding", "code/retrieval"):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)

if "embed_model" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "embed_model", ROOT / "code" / "embedding" / "model.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["embed_model"] = mod
    spec.loader.exec_module(mod)
