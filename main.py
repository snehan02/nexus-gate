# FastAPI Entry point
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from litellm import completion
from app.security import scrub_pii, is_jailbreak, pre_request_judge, log_security_violation # Import Judge logic
from app.triage import get_optimal_model
from app.observability import record_metric, should_break_circuit, calculate_observability, get_p99_latency

load_dotenv(override=True)
app = FastAPI(title="Nexus AI Gateway")

class UserPrompt(BaseModel):
    user_id: str
    text: str
    priority: str = "standard"

@app.post("/v1/chat")
async def chat_gateway(payload: UserPrompt):
    # 0. Circuit Breaker Check
    # (Just a log for now as requested, but we can failover here)
    
    # 0. Advanced Security Guardrail (LLM-as-a-Judge)
    judge_result = await pre_request_judge(payload.text)
    if judge_result.get("verdict") == "DANGER":
        log_security_violation(payload.user_id, judge_result.get("reason"), judge_result.get("risk_score"))
        raise HTTPException(status_code=403, detail=f"Security violation detected: {judge_result.get('reason')}")

    # 1. Legacy Security Check
    if is_jailbreak(payload.text):
        raise HTTPException(status_code=403, detail="Security violation detected (Heuristic).")
    
    # 2. Scrub PII
    safe_prompt = scrub_pii(payload.text)

    # 3. Triage (Model Selection)
    selected_model = get_optimal_model(safe_prompt, payload.priority)

    # Check circuit status before calling provider
    is_failing = should_break_circuit(selected_model)
    if is_failing:
        print(f"⚠️ [CIRCUIT BREAKER] {selected_model} is underperforming. Attempting failover...")
        # (In 2026, we automatically switch to the fallback)
        selected_model = "gemini/gemini-1.5-flash"

    # 4. Execute with LiteLLM (Auto-failover included)
    start_time = time.time()
    try:
        if os.getenv("MOCK_AI", "false").lower() == "true":
            # Simulate first token latency
            time.sleep(0.4) 
            ttft = time.time() - start_time
            time.sleep(0.1) # Rest of response
            
            end_time = time.time()
            record_metric(selected_model, end_time - start_time)
            
            return {
                "user_id": payload.user_id,
                "model_assigned": selected_model,
                "response": f"[MOCK MODE] Simulated response for: '{safe_prompt}'",
                "telemetry": {
                    "ttft_ms": float(f"{(ttft * 1000):.2f}"),
                    "tokens_per_sec": 45.2,
                    "provider_health": "stable" if not is_failing else "recovering"
                }
            }

        response = completion(
            model=selected_model,
            messages=[{"role": "user", "content": safe_prompt}],
            fallbacks=["gemini/gemini-1.5-flash"] # Fixed provider name
        )
        end_time = time.time()
        
        # Record and Track
        record_metric(selected_model, end_time - start_time)
        metrics = calculate_observability(start_time, end_time, response.usage.total_tokens)
        
        return {
            "user_id": payload.user_id,
            "model_assigned": selected_model,
            "response": response.choices[0].message.content,
            "telemetry": {
                "ttft_ms": float(f"{(metrics['ttft'] * 1000):.2f}"),
                "tokens_per_sec": metrics["tokens_per_sec"],
                "p99_latency_ms": float(f"{(get_p99_latency(selected_model) * 1000):.2f}")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)