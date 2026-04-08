import sys
import json
import tiktoken
from app.triage import route

PRICING = {
    "capable": 0.075 / 1_000_000,
    "fast":    0.050 / 1_000_000,
}
enc = tiktoken.get_encoding("cl100k_base")

def estimate_cost(text, model):
    tokens = len(enc.encode(text))
    return tokens * PRICING[model]

with open('prompts.json') as f:
    suite = json.load(f)

results = []
for item in suite:
    prompt_text = item["prompt"]
    decision = route(prompt_text)
    results.append({
        "prompt": prompt_text,
        "routed_to": decision["model"]
    })

smart_cost    = sum(estimate_cost(r['prompt'], r['routed_to']) for r in results)
baseline_cost = sum(estimate_cost(r['prompt'], 'capable')        for r in results)
saving_pct    = (baseline_cost - smart_cost) / baseline_cost * 100 if baseline_cost > 0 else 0

print(f"Baseline: ${baseline_cost:.8f}")
print(f"Smart: ${smart_cost:.8f}")
print(f"Saving: {saving_pct:.2f}%")
