import json
from app.triage import route

with open('prompts.json') as f:
    suite = json.load(f)

results = []
for item in suite:
    prompt_text = item["prompt"]
    decision = route(prompt_text)
    routed_to = decision["model"]
    expected  = "capable" if item["label"] == "complex" else "fast"
    correct   = routed_to == expected
    results.append({
        "id": item["id"],
        "correct": correct,
        "routed_to": routed_to,
        "expected": expected,
        "score": decision["score"]
    })

total = len(results)
correct_count = sum(1 for r in results if r["correct"])
accuracy = correct_count / total

print(f"Accuracy: {accuracy:.0%}")
print(f"Correct: {correct_count}/{total}")

wrong = [r for r in results if not r["correct"]]
for r in wrong:
    print(f"MIS-ROUTE: ID {r['id']}, Expected {r['expected']}, Got {r['routed_to']}, Score {r['score']}")
