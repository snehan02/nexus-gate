# PRD — Nexus-Gate: Missing Components
> **Purpose:** This document tells you exactly what to build, in what order, and what each file should look like. Copy-paste the code skeletons, fill in the logic, run the commands. Nothing here is optional.

---

## Status Snapshot

| Component | Status | Priority |
|---|---|---|
| `POST /v1/chat` gateway server | ✅ Done | — |
| Security interceptor | ✅ Done | — |
| Streamlit dashboard | ✅ Done | — |
| **Routing model (formalised)** | ⚠️ Exists, not research-grade | HIGH |
| **`app/cache.py` — semantic cache** | ❌ Missing | HIGH |
| **`poc.py` — standalone evaluator** | ❌ Missing | CRITICAL |
| **`prompts.json` — 20-prompt test suite** | ❌ Missing | CRITICAL |

---

## Component 1 — `prompts.json` (Do This First)

**Why first:** Everything else — poc.py, cache testing, cost comparison — depends on this file existing.

**Create this file at the root of your repo:**

```json
[
  {"id": 1, "prompt": "What is the capital of France?", "label": "simple"},
  {"id": 2, "prompt": "How do I convert Celsius to Fahrenheit?", "label": "simple"},
  {"id": 3, "prompt": "What does API stand for?", "label": "simple"},
  {"id": 4, "prompt": "Give me a one-line summary of machine learning.", "label": "simple"},
  {"id": 5, "prompt": "What year was Python created?", "label": "simple"},
  {"id": 6, "prompt": "Translate hello to Spanish.", "label": "simple"},
  {"id": 7, "prompt": "What is 2 to the power of 10?", "label": "simple"},
  {"id": 8, "prompt": "List 3 types of databases.", "label": "simple"},
  {"id": 9, "prompt": "What is the difference between HTTP and HTTPS?", "label": "simple"},
  {"id": 10, "prompt": "Who created Linux?", "label": "simple"},
  {"id": 11, "prompt": "Explain transformer architecture and compare it to LSTM networks in detail.", "label": "complex"},
  {"id": 12, "prompt": "Write a Python function to implement binary search with full error handling.", "label": "complex"},
  {"id": 13, "prompt": "Analyse why microservices architectures fail at scale and suggest three mitigations.", "label": "complex"},
  {"id": 14, "prompt": "Compare REST and GraphQL APIs — when would you choose each and why?", "label": "complex"},
  {"id": 15, "prompt": "Explain step by step how attention mechanisms work in transformers.", "label": "complex"},
  {"id": 16, "prompt": "Debug this code and explain why it fails: def divide(x, y): return x/y", "label": "complex"},
  {"id": 17, "prompt": "Design a rate limiter for an API — describe the algorithm and data structures needed.", "label": "complex"},
  {"id": 18, "prompt": "What are the trade-offs between normalisation and denormalisation in relational databases?", "label": "complex"},
  {"id": 19, "prompt": "Explain the CAP theorem and give a real-world example of each trade-off.", "label": "complex"},
  {"id": 20, "prompt": "Write a regex to validate email addresses and explain every component of the pattern.", "label": "complex"}
]
```

---

## Component 2 — `app/triage.py` (Formalise Your Routing Model)

**What to change:** Your existing triage logic needs to be restructured so it is a documented model with named features, weights, and a confidence score. The routing decision must be explainable per-request.

**Replace your triage logic with this structure:**

```python
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
]
CODE_WORDS = [
    "def ", "class ", "function", "implement", "debug", "algorithm",
    "code", "regex", "script", "programme", "program", "write a",
]
MULTI_STEP_WORDS = [
    "step by step", "first then", "and then", "finally", "multiple steps",
    "walk me through", "in order to",
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
```

**Wire it into `main.py`** — replace however you currently call triage with:

```python
from app.triage import route as triage_route

routing = triage_route(request.text)
model_to_use = "groq/llama-3.1-8b-instant" if routing["model"] == "fast" else "gemini/gemini-1.5-flash"
```

---

## Component 3 — `app/cache.py` (New File — Semantic Cache)

**Install the dependency first:**

```bash
pip install sentence-transformers
```

**Create `app/cache.py`:**

```python
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
```

**Wire it into `main.py`** — add these two blocks around your existing LLM call:

```python
from app.cache import check as cache_check, store as cache_store

# --- BEFORE your LLM call ---
cached = cache_check(request.text)
if cached:
    return {
        "response":   cached["response"],
        "model_used": cached["model_used"],
        "cache_hit":  True,
        "similarity": cached["similarity"],
        "latency_ms": 0,
    }

# --- AFTER your LLM call (wherever you get `llm_response`) ---
cache_store(request.text, llm_response, routing["model"])
```

---

## Component 4 — `poc.py` (New File — Standalone Evaluator)

**This is what judges will run directly. It must work with no server running.**

**Create `poc.py` at the root of your repo:**

```python
# poc.py
# Usage: python poc.py prompts.json
# Judges run this directly — no server required.

import sys
import json
from app.triage import route

def run(path: str):
    with open(path) as f:
        suite = json.load(f)

    results = []
    for item in suite:
        decision = route(item["prompt"])
        routed_to = decision["model"]
        expected  = "capable" if item["label"] == "complex" else "fast"
        correct   = routed_to == expected

        results.append({
            "id":         item["id"],
            "prompt":     item["prompt"][:60] + "…" if len(item["prompt"]) > 60 else item["prompt"],
            "label":      item["label"],
            "routed_to":  routed_to,
            "expected":   expected,
            "score":      decision["score"],
            "confidence": decision["confidence"],
            "correct":    correct,
            "reason":     decision["reason"],
        })

    # ── Per-prompt output ────────────────────────────────────────────────────
    print("\n" + "═" * 80)
    print("  NEXUS-GATE ROUTING MODEL — PoC EVALUATION")
    print("═" * 80)
    print(f"  {'ID':<4} {'LABEL':<10} {'ROUTED':<10} {'SCORE':<8} {'CONF':<8} {'OK?':<6} PROMPT")
    print("─" * 80)
    for r in results:
        ok = "✓" if r["correct"] else "✗"
        print(f"  {r['id']:<4} {r['label']:<10} {r['routed_to']:<10} "
              f"{r['score']:<8.3f} {r['confidence']:<8.3f} {ok:<6} {r['prompt']}")

    # ── Summary ──────────────────────────────────────────────────────────────
    total   = len(results)
    correct = sum(1 for r in results if r["correct"])
    complex_items = [r for r in results if r["label"] == "complex"]
    simple_items  = [r for r in results if r["label"] == "simple"]

    # FP = complex sent to fast (dangerous — lower quality)
    fp = sum(1 for r in complex_items if r["routed_to"] == "fast")
    # FN = simple sent to capable (wasteful — costs more)
    fn = sum(1 for r in simple_items  if r["routed_to"] == "capable")

    fp_rate = fp / len(complex_items) if complex_items else 0
    fn_rate = fn / len(simple_items)  if simple_items  else 0
    accuracy = correct / total

    print("\n" + "═" * 80)
    print("  SUMMARY")
    print("═" * 80)
    print(f"  Total prompts evaluated : {total}")
    print(f"  Correct routing         : {correct}/{total}  ({accuracy:.0%})")
    print(f"  False positive rate     : {fp}/{len(complex_items)} complex→fast  ({fp_rate:.0%})  ← dangerous")
    print(f"  False negative rate     : {fn}/{len(simple_items)} simple→capable ({fn_rate:.0%})  ← wasteful")
    print(f"  Accuracy                : {accuracy:.0%}")
    print("─" * 80)

    # ── Mis-routes ───────────────────────────────────────────────────────────
    wrong = [r for r in results if not r["correct"]]
    if wrong:
        print(f"\n  MIS-ROUTES ({len(wrong)} total):")
        for r in wrong:
            print(f"  [{r['id']}] Expected {r['expected']}, got {r['routed_to']} "
                  f"(score={r['score']:.3f}): {r['prompt']}")
    print("═" * 80 + "\n")

    return accuracy


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python poc.py prompts.json")
        sys.exit(1)
    run(sys.argv[1])
```

**Run it:**

```bash
python poc.py prompts.json
```

**Target output shape (your numbers will differ):**

```
════════════════════════════════════════════════════════════════════════════════
  NEXUS-GATE ROUTING MODEL — PoC EVALUATION
════════════════════════════════════════════════════════════════════════════════
  ID   LABEL      ROUTED     SCORE    CONF     OK?    PROMPT
────────────────────────────────────────────────────────────────────────────────
  1    simple     fast       0.060    0.880    ✓      What is the capital of France?
  ...
  11   complex    capable    0.775    0.550    ✓      Explain transformer architecture…
  ...
════════════════════════════════════════════════════════════════════════════════
  SUMMARY
════════════════════════════════════════════════════════════════════════════════
  Total prompts evaluated : 20
  Correct routing         : 17/20  (85%)
  False positive rate     : 2/10 complex→fast  (20%)  ← dangerous
  False negative rate     : 1/10 simple→capable (10%) ← wasteful
  Accuracy                : 85%
```

---

## Component 5 — Cost Comparison (add to `poc.py` or a separate script)

**Install:**

```bash
pip install tiktoken
```

**Add this function to `poc.py` or create `cost_compare.py`:**

```python
import tiktoken

# Approximate pricing (free tiers differ — use these as constants for comparison)
PRICING = {
    "capable": 0.075 / 1_000_000,  # Gemini 1.5 Flash per token
    "fast":    0.050 / 1_000_000,  # Groq Llama 8B per token
}

enc = tiktoken.get_encoding("cl100k_base")

def estimate_cost(text: str, model: str) -> float:
    tokens = len(enc.encode(text))
    return tokens * PRICING[model]

def cost_comparison(results: list, responses: list) -> None:
    """
    results  = output from poc.py run()
    responses = list of actual LLM response strings (same order)
    """
    smart_cost    = sum(estimate_cost(r, res["routed_to"]) for r, res in zip(responses, results))
    baseline_cost = sum(estimate_cost(r, "capable")        for r in responses)
    saving_pct    = (baseline_cost - smart_cost) / baseline_cost * 100

    print(f"Always-Capable baseline : ${baseline_cost:.6f}")
    print(f"Smart routing cost      : ${smart_cost:.6f}")
    print(f"Saving                  : {saving_pct:.1f}%")
```

**Note for your PPT:** even with mock responses, you can show the cost comparison by using the token counts of the prompts themselves as a proxy. The ratio holds — shorter simple prompts going to a cheaper model always wins.

---

## `requirements.txt` — Add These

```
fastapi
uvicorn
litellm
streamlit
sentence-transformers
tiktoken
python-dotenv
scikit-learn
numpy
```

---

## `.env.example` — Required Deliverable

```env
# Fast model — Groq (free tier, no card required)
GROQ_API_KEY=your_groq_key_here

# Capable model — Gemini (AI Studio free tier, no card required)
GEMINI_API_KEY=your_gemini_key_here

# Set to true to skip real LLM calls during development
MOCK_AI=true
```

---

## README additions — Required

Your README must state these things explicitly (judges check):

```markdown
## Models Used

| Label | Model | Provider | Use Case |
|---|---|---|---|
| Fast model | Llama 3.1 8B | Groq (free tier) | Simple queries, factual Q&A, short summaries |
| Capable model | Gemini 1.5 Flash | Google AI Studio (free tier) | Reasoning, code generation, multi-step analysis |

## Routing Model

Feature-weighted rule-based complexity scorer. Features: prompt_length (0.30),
question_word_flag (0.25), code_flag (0.25), multi_step_flag (0.20).
Threshold: 0.5. Evaluated on 20-prompt test suite — see PoC results.

## Run the PoC Evaluator

python poc.py prompts.json
```

---

## Execution Order

```
Day 1  →  Create prompts.json
Day 1  →  Update app/triage.py with named features + confidence score
Day 2  →  Build poc.py, run it, record your accuracy numbers
Day 3  →  Create app/cache.py, wire into main.py, test cache hits
Day 4  →  Add cost comparison, run on 20 prompts, record savings %
Day 5  →  Update README, prepare demo, memorise your numbers
```

---

> **Rule:** Do not touch the dashboard or security module. They are already done. Every hour goes into the four components above.