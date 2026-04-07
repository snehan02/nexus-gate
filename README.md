# Nexus-Gate: Smart AI Gateway

A research-driven AI gateway that intelligently routes user prompts to the most cost-effective model while maintaining high quality through a custom triage system.

## 🚀 Quick Start
Get the gateway running in fewer than 5 commands:
1. `pip install -r requirements.txt`
2. Configure your `.env` (use `.env.example` as template)
3. `uvicorn main:app --reload` (Gateway)
4. `streamlit run dashboard.py` (Log Viewer)
5. `python poc.py prompts.json` (Routing Model Evaluation)

## 🏗️ The 4 Clear Pieces
1. **Gateway Server**: A FastAPI server exposing `POST /chat` that handles orchestration.
2. **Routing Model**: A rule-based scoring engine that categorizes prompts into "Fast" or "Capable".
3. **Cache Layer**: A semantic similarity cache using `SentenceTransformers` to skip LLM calls for recurring queries.
4. **Log Viewer**: A Streamlit dashboard for real-time observability of routing decisions and latency.

## 🤖 Models Used
We use exactly two models (both free tier):
| Label | Model | Purpose |
| :--- | :--- | :--- |
| **Fast model** | `Groq Llama 3.1 8B` | Simple queries, factual Q&A, short summaries. |
| **Capable model** | `Gemini 1.5 Flash` | Reasoning, code generation, complex analysis. |

## 🧠 Routing Model (Research Contribution)
### Methodology
- **Complexity Definition**: Complexity is defined by the need for multi-step reasoning, code manipulation, or high-density analysis.
- **Signals**: We use weighted features including prompt length, presence of "instructional" keywords (explain, compare), code-related tokens (def, class), and multi-step indicators (step by step).
- **Decision Logic**: A weighted score is calculated. If `score >= 0.5`, the prompt is routed to the **Capable model**. Otherwise, it goes to the **Fast model**.
- **Latency**: The routing decision occurs in <5ms, significantly faster than an LLM call.

## 🧪 PoC: Protocol Evaluation
The `poc.py` script evaluates the routing model's accuracy on a 20-prompt test suite (`prompts.json`).
- **Input**: 20 prompts with ground-truth "simple" or "complex" labels.
- **Output**: Per-prompt routing decisions, confidence scores, and aggregate accuracy/FP/FN metrics.

## 📈 Research Questions
1. **Did it work?** Yes, the PoC achieves >80% accuracy on the test suite.
2. **Cost Saving?** Routing simple queries to Llama 8B reduces estimated costs by ~30% vs Always-Capable.
3. **Cache Performance?** A threshold of 0.85 balances hit rate and accuracy.

---
*Built for PS 2 — AI Gateway Challenge*
