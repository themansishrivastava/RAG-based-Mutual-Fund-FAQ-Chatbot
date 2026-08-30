"""Single embedding model for ingest and query (PRD)."""

from __future__ import annotations

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str], show_progress_bar: bool = False) -> list[list[float]]:
    model = get_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=show_progress_bar)
    if vectors.ndim != 2:
        raise ValueError("expected a 2D embedding matrix")
    dims = {len(row) for row in vectors}
    if len(dims) != 1:
        raise ValueError("embedding dimensionality must be the same for all chunks")
    return vectors.tolist()
