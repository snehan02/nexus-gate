# FastAPI Entry point
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from litellm import completion
from app.security import scrub_pii
from app.triage import route as triage_route
from app.cache import check as cache_check, store as cache_store
from app.observability import record_metric, log_request

load_dotenv(override=True)
app = FastAPI(title="Nexus AI Gateway")

class UserPrompt(BaseModel):
    user_id: str
    text: str

@app.post("/chat")
async def chat_gateway(payload: UserPrompt):
    start_time = time.time()
    
    # 1. Scrub PII
    safe_prompt = scrub_pii(payload.text)

    # 2. Cache Check
    cached = cache_check(safe_prompt)
    if cached:
        latency_ms = (time.time() - start_time) * 1000
        log_request(safe_prompt, cached["model_used"], "Cache Hit", latency_ms, True, {"cache_similarity": cached.get("similarity")})
        return {
            "response": cached["response"],
            "model_used": cached["model_used"],
            "routing_reason": "Semantic cache hit",
            "latency_ms": round(latency_ms, 2),
            "cache_hit": True
        }

    # 3. Triage (Model Selection)
    routing = triage_route(safe_prompt)
    # Map to actual model strings (Free tiers)
    selected_model = "groq/llama-3.1-8b-instant" if routing["model"] == "fast" else "gemini/gemini-1.5-flash"
    
    # Identify friendly names for logging/matching user request
    model_label = "Fast model" if routing["model"] == "fast" else "Capable model"

    # 4. Execute (Mock or Real)
    if os.getenv("MOCK_AI", "false").lower() == "true":
        # Simulate a delay
        time.sleep(0.5)
        llm_response = f"[MOCK RESPONSE] This is a simulated response from the {model_label} ({selected_model})."
        latency_ms = (time.time() - start_time) * 1000
        
        log_request(safe_prompt, model_label, routing["reason"], latency_ms, False, routing["features"])
        cache_store(safe_prompt, llm_response, model_label)
        
        return {
            "response": llm_response,
            "model_used": model_label,
            "routing_reason": routing["reason"],
            "latency_ms": round(latency_ms, 2),
            "cache_hit": False
        }

    # 4. Execute with LiteLLM
    try:
        response = completion(
            model=selected_model,
            messages=[{"role": "user", "content": safe_prompt}],
        )
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Record and Track
        record_metric(selected_model, end_time - start_time)
        log_request(safe_prompt, model_label, routing["reason"], latency_ms, False, routing["features"])
        
        llm_response = response.choices[0].message.content
        cache_store(safe_prompt, llm_response, model_label)
        
        return {
            "response": llm_response,
            "model_used": model_label,
            "routing_reason": routing["reason"],
            "latency_ms": round(latency_ms, 2),
            "cache_hit": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)