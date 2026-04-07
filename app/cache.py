# app/cache.py

import numpy as np
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")  # 22MB, runs on CPU, <10ms per embed

# ── Research variable: tune this and report the impact in your PPT ───────────
# 0.70 = loose (high hit rate, risk of wrong answers)
# 0.85 = balanced (recommended)
# 0.95 = strict (high accuracy, low hit rate)
THRESHOLD = 0.85

_store: list[dict] = []  # [{embedding, response, prompt, model_used}]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def check(prompt: str) -> dict | None:
    """
    Returns cached entry if a semantically similar prompt exists, else None.
    Entry shape: {response, prompt, model_used, similarity}
    """
    if not _store:
        return None

    emb = _model.encode(prompt, convert_to_numpy=True)
    best, best_score = None, 0.0

    for entry in _store:
        sim = _cosine(emb, entry["embedding"])
        if sim > best_score:
            best_score = sim
            best = entry

    if best_score >= THRESHOLD:
        return {**best, "similarity": round(best_score, 4)}
    return None


def store(prompt: str, response: str, model_used: str) -> None:
    """Store a prompt-response pair after a successful LLM call."""
    _store.append({
        "embedding":  _model.encode(prompt, convert_to_numpy=True),
        "prompt":     prompt,
        "response":   response,
        "model_used": model_used,
    })


def stats() -> dict:
    return {"stored_entries": len(_store), "threshold": THRESHOLD}
