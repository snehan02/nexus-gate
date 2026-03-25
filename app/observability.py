import time
import statistics
from collections import deque

# Metrics storage (in-memory mock for 2026 AI Gateway)
model_latencies = {} # model_name -> deque of latencies
CIRCUIT_THRESHOLD_MS = 1500 # If p99 > 1.5s, break
MAX_HISTORY = 100

def record_metric(model_name: str, latency: float):
    """
    Records a latency metric for a specific model.
    :param model_name: The name of the AI model.
    :param latency: Latency in seconds.
    """
    if model_name not in model_latencies:
        model_latencies[model_name] = deque(maxlen=MAX_HISTORY)
    model_latencies[model_name].append(latency)
    print(f"📈 [METRIC] {model_name}: {latency*1000:.2f}ms")

def should_break_circuit(model_name: str) -> bool:
    """
    Determines if the circuit breaker should be triggered.
    Based on p99 latency exceeding threshold.
    """
    if model_name not in model_latencies or len(model_latencies[model_name]) < 5:
        return False # Not enough data
    
    p99 = get_p99_latency(model_name)
    return (p99 * 1000) > CIRCUIT_THRESHOLD_MS

def get_p99_latency(model_name: str) -> float:
    """
    Calculates the p99 latency for a model.
    """
    if model_name not in model_latencies or not model_latencies[model_name]:
        return 0.0
    
    latencies = sorted(list(model_latencies[model_name]))
    idx = int(0.99 * (len(latencies) - 1))
    return latencies[idx]

def calculate_observability(start_time, end_time, total_tokens):
    """
    Calculates key observability metrics for a request.
    """
    duration = end_time - start_time
    # Mock TTFT (Time To First Token)
    ttft = duration * 0.35 
    
    tokens_per_sec = total_tokens / duration if duration > 0 else 0
    
    return {
        "duration": duration,
        "ttft": ttft,
        "tokens_per_sec": round(tokens_per_sec, 2)
    }
