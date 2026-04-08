import json
import time
from app.cache import check, store

# Mock some stores
prompts = [
    "What is the capital of France?",
    "How do I convert Celsius to Fahrenheit?",
    "What is the capital of France?" # Duplicate
]

results = []
for p in prompts:
    cached = check(p)
    if cached:
        results.append({"prompt": p, "hit": True, "similarity": cached["similarity"]})
    else:
        results.append({"prompt": p, "hit": False})
        store(p, "Mock response", "fast")

print(json.dumps(results, indent=2))

# Test boundary case
p_exact = "What is the capital of France?"
p_near = "What's the capital of France?" # Slight variation

print("\nExact match check:")
print(f"Result: {check(p_exact) is not None}")

print("\nNear match check (Threshold 0.85):")
res_near = check(p_near)
if res_near:
    print(f"Hit! Similarity: {res_near['similarity']}")
else:
    # Manual check similarity
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer("all-MiniLM-L6-v2")
    emb1 = model.encode(p_exact)
    emb2 = model.encode(p_near)
    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    print(f"Miss. Similarity was {sim:.4f}")
