# 🛡️ Nexus AI Gateway

**Nexus AI Gateway** is a high-performance, secure, and observable middleware for LLM applications. It provides intelligent triage, advanced security guardrails, and a live governance dashboard to manage AI traffic efficiently and safely.

## 🚀 Key Features

- **Intelligent Triage**: Automatically routes prompts to the most cost-effective and capable models (e.g., GPT-4o-mini for simple tasks, Claude 3.5 Sonnet for complex ones).
- **Security Guardrails**: Heuristic and LLM-as-a-Judge based protection against jailbreaks, PII leaks, and prompt injections.
- **Circuit Breaker & Fallbacks**: Built-in resilience with automatic failover to stable models (like Gemini 1.5 Flash) during provider outages.
- **Live Governance Dashboard**: Real-time observability into traffic, performance (TTFT), security blocks, and financial ROI.
- **Cost Optimization**: Drastically reduces API costs by using adaptive triage rather than flat-rate "pro" models.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- A virtual environment (recommended)

### 2. Clone and Install
```bash
# Clone the repository (if applicable)
cd nexus-gate

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory (or update the existing one):
```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
MOCK_AI=true  # Set to 'false' to use real LLM providers
```

---

## 🚦 Running the Project

### Start the AI Gateway (FastAPI)
The gateway handles incoming chat requests and applies governance logic.
```bash
python main.py
# OR
uvicorn main:app --reload
```
- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Endpoint**: `POST /v1/chat`

### Start the Live Ops Dashboard (Streamlit)
The dashboard provides a visual interface for system monitoring.
```bash
streamlit run dashboard.py
```
- **Dashboard URL**: [http://localhost:8501](http://localhost:8501)

---

## 🧪 Testing the Gateway
You can test the gateway using `curl` or PowerShell:

### PowerShell
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/chat `
  -ContentType "application/json" `
  -Body '{"user_id": "demo_user", "text": "Hello Nexus!", "priority": "standard"}'
```

### cURL
```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"user_id": "demo_user", "text": "Hello Nexus!", "priority": "standard"}'
```

---

## 📂 Project Structure
- `main.py`: Entry point for the FastAPI gateway.
- `dashboard.py`: Streamlit dashboard for live governance.
- `app/`:
  - `security.py`: Logic for jailbreak detection, PII scrubbing, and pre-request judging.
  - `triage.py`: Model selection and routing logic.
  - `observability.py`: Metrics tracking, circuit breaker status, and latency calculations.
- `.env`: Secret management and feature flags.
