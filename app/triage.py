# app/triage.py

import re
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Semantic Anchors (pre-calculated at module level) ────────────────────────
_model = SentenceTransformer("all-MiniLM-L6-v2")

SIMPLE_ANCHORS = [
    "What is the capital of France?",
    "How do I convert Celsius to Fahrenheit?",
    "What year was Python created?",
    "Translate hello to Spanish.",
    "What is 2 to the power of 10?",
]

COMPLEX_ANCHORS = [
    "Explain transformer architecture and compare it to LSTM networks in detail.",
    "Write a Python function to implement binary search with full error handling.",
    "Analyse why microservices architectures fail at scale and suggest three mitigations.",
    "Compare REST and GraphQL APIs — when would you choose each and why?",
    "Explain the CAP theorem and give a real-world example of each trade-off.",
]

SIMPLE_EMBS = _model.encode(SIMPLE_ANCHORS, convert_to_numpy=True)
COMPLEX_EMBS = _model.encode(COMPLEX_ANCHORS, convert_to_numpy=True)

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    # Handle both single vector and matrix of vectors
    if a.ndim == 1 and b.ndim == 2:
        return np.dot(b, a) / (np.linalg.norm(b, axis=1) * np.linalg.norm(a) + 1e-9)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

# ── Feature weights (research decision, documented) ──────────────────────────
# Updated weights to include semantic anchor scoring.
WEIGHTS = {
    "prompt_length":    0.10,  # reduced from 0.30
    "question_word":    0.25,  
    "code_flag":        0.25,
    "multi_step_flag":  0.20,
    "semantic_anchor":  0.20,  # new semantic feature
}
THRESHOLD = 0.5
MAX_LENGTH = 500  

QUESTION_WORDS = [
    "explain", "compare", "analyse", "analyze", "difference between",
    "why does", "how does", "what causes", "evaluate", "discuss",
    "trade-offs", "pros and cons", "mitigations", "describe",
    "write", "how",
]
CODE_WORDS = [
    "def ", "class ", "function", "implement", "debug", "algorithm",
    "code", "regex", "script", "programme", "program", "write a",
    "architecture", "microservices", "rest", "graphql", "api", "database",
    "transformer", "lstm", "neural", "binary search", "data structure",
    "normalisation", "denormalisation", "cap theorem", "python",
]
MULTI_STEP_WORDS = [
    "step by step", "first then", "and then", "finally", "multiple steps",
    "walk me through", "in order to", "process of", "how to implement",
    "implement", "write a",
]


def _extract_features(prompt: str) -> dict:
    """Return named feature values for a given prompt."""
    lower = prompt.lower()
    
    # 1. Text-based features
    features = {
        "prompt_length":   min(len(prompt) / MAX_LENGTH, 1.0),
        "question_word":   1.0 if any(w in lower for w in QUESTION_WORDS) else 0.0,
        "code_flag":       1.0 if any(w in lower for w in CODE_WORDS) else 0.0,
        "multi_step_flag": 1.0 if any(w in lower for w in MULTI_STEP_WORDS) else 0.0,
    }

    # 2. Semantic feature
    emb = _model.encode(prompt, convert_to_numpy=True)
    simple_sim = np.max(_cosine(emb, SIMPLE_EMBS))
    complex_sim = np.max(_cosine(emb, COMPLEX_EMBS))
    
    # Normalise complex_sim - simple_sim from [-1, 1] to [0, 1]
    features["semantic_anchor"] = float(max(0.0, min(1.0, (complex_sim - simple_sim + 1) / 2)))
    
    return features


def route(prompt: str) -> dict:
    """
    Returns routing decision with full metadata.
    """
    features = _extract_features(prompt)

    score = sum(WEIGHTS[k] * v for k, v in features.items())
    decision = "capable" if score >= THRESHOLD else "fast"
    confidence = round(abs(score - THRESHOLD) * 2, 3)

    # Escalation Rule: if confidence < 0.20, force to capable model
    escalated = False
    if confidence < 0.20:
        decision = "capable"
        escalated = True

    fired = [k for k, v in features.items() if v > 0]
    reason = (
        f"Score {score:.2f} {'+=' if score >= THRESHOLD else '<'} {THRESHOLD} → {decision} model. "
        f"Features fired: {', '.join(fired) or 'none'}."
    )
    if escalated:
        reason += " [escalated: low confidence]"

    return {
        "model":      decision,
        "score":      round(score, 3),
        "confidence": confidence,
        "features":   features,
        "reason":     reason,
    }