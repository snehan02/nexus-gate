from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
p1 = "What is the capital of France?"
p2 = "Tell me the capital of France."
p3 = "Capital of France?"

emb1 = model.encode(p1)
emb2 = model.encode(p2)
emb3 = model.encode(p3)

def sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print(f"p1 vs p2: {sim(emb1, emb2):.4f}")
print(f"p1 vs p3: {sim(emb1, emb3):.4f}")
