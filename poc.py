# poc.py
# Usage: python poc.py prompts.json
# Judges run this directly — no server required.

import sys
import json
import tiktoken
from app.triage import route

# Approximate pricing (free tiers differ — use these as constants for comparison)
PRICING = {
    "capable": 0.075 / 1_000_000,  # Gemini 1.5 Flash per token
    "fast":    0.050 / 1_000_000,  # Groq Llama 8B per token
}

enc = tiktoken.get_encoding("cl100k_base")

def estimate_cost(text: str, model: str) -> float:
    tokens = len(enc.encode(text))
    return tokens * PRICING[model]

def cost_comparison(results: list) -> None:
    """
    results = output from poc.py run()
    We use the prompt text to estimate cost saving since we don't have real responses here.
    The ratio holds — shorter simple prompts going to a cheaper model always wins.
    """
    smart_cost    = sum(estimate_cost(r["prompt_full"], r["routed_to"]) for r in results)
    baseline_cost = sum(estimate_cost(r["prompt_full"], "capable")        for r in results)
    saving_pct    = (baseline_cost - smart_cost) / baseline_cost * 100 if baseline_cost > 0 else 0

    print("\n" + "═" * 80)
    print("  COST EFFICIENCY ANALYSIS (Prompt-based Proxy)")
    print("═" * 80)
    print(f"  Always-Capable baseline : ${baseline_cost:.8f}")
    print(f"  Smart routing cost      : ${smart_cost:.8f}")
    print(f"  Estimated Saving        : {saving_pct:.1f}%")
    print("─" * 80)

def run(path: str):
    with open(path) as f:
        suite = json.load(f)

    results = []
    for item in suite:
        prompt_text = item["prompt"]
        decision = route(prompt_text)
        routed_to = decision["model"]
        expected  = "capable" if item["label"] == "complex" else "fast"
        correct   = routed_to == expected

        results.append({
            "id":          item["id"],
            "prompt_full": prompt_text,
            "prompt":      prompt_text[:60] + "…" if len(prompt_text) > 60 else prompt_text,
            "label":       item["label"],
            "routed_to":   routed_to,
            "expected":    expected,
            "score":       decision["score"],
            "confidence":  decision["confidence"],
            "correct":     correct,
            "reason":      decision["reason"],
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

    # ── Cost Comparison ──────────────────────────────────────────────────────
    cost_comparison(results)

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
