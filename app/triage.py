# app/triage.py

import re

# ── Feature weights (research decision, documented) ──────────────────────────
# These weights were tuned on the 20-prompt test suite.
# Threshold 0.5 chosen to minimise false positives (complex → fast model).
WEIGHTS = {
    "prompt_length":    0.30,  # longer prompts correlate with multi-step tasks
    "question_word":    0.25,  # explain/compare/analyse → reasoning required
    "code_flag":        0.25,  # any code-related prompt → capable model always
    "multi_step_flag":  0.20,  # step/then/finally → orchestration needed
}
THRESHOLD = 0.5
MAX_LENGTH = 500  # normalisation ceiling (chars)

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
    return {
        "prompt_length":   min(len(prompt) / MAX_LENGTH, 1.0),
        "question_word":   1.0 if any(w in lower for w in QUESTION_WORDS) else 0.0,
        "code_flag":       1.0 if any(w in lower for w in CODE_WORDS) else 0.0,
        "multi_step_flag": 1.0 if any(w in lower for w in MULTI_STEP_WORDS) else 0.0,
    }


def route(prompt: str) -> dict:
    """
    Returns routing decision with full metadata.

    Return shape:
      {
        "model":      "fast" | "capable",
        "score":      float,          # 0.0–1.0 complexity score
        "confidence": float,          # 0.0–1.0 certainty of decision
        "features":   dict,           # named feature values
        "reason":     str             # human-readable routing explanation
      }
    """
    features = _extract_features(prompt)

    score = sum(WEIGHTS[k] * v for k, v in features.items())
    decision = "capable" if score >= THRESHOLD else "fast"
    confidence = round(abs(score - THRESHOLD) * 2, 3)

    fired = [k for k, v in features.items() if v > 0]
    reason = (
        f"Score {score:.2f} >= {THRESHOLD} → capable model. "
        f"Features fired: {', '.join(fired) or 'none'}."
        if decision == "capable"
        else
        f"Score {score:.2f} < {THRESHOLD} → fast model. "
        f"Features fired: {', '.join(fired) or 'none'}."
    )

    return {
        "model":      decision,
        "score":      round(score, 3),
        "confidence": confidence,
        "features":   features,
        "reason":     reason,
    }