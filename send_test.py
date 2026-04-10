# send_test.py
import requests
import time

URL = "http://localhost:8000/chat"

PROMPTS = [
    "What is 2+2?",
    "Explain quantum entanglement in simple terms",
    "Write a Python script to calculate Fibonacci using recursion and explain it"
]

def send_tests():
    print(f"🚀 Sending {len(PROMPTS)} test requests to the Gateway at {URL}...")
    
    for i, p in enumerate(PROMPTS):
        try:
            payload = {"user_id": "demo_user", "text": p}
            start = time.time()
            res = requests.post(URL, json=payload)
            latency = (time.time() - start) * 1000
            
            data = res.json()
            print(f"\n[{i+1}] Prompt: {p}")
            print(f"    Routed to : {data.get('model_used')}")
            print(f"    Reason    : {data.get('routing_reason')}")
            print(f"    Latency   : {latency:.0f}ms")
        except Exception as e:
            print(f"    Error: {e}")
            print("    Is main.py running at http://localhost:8000?")

    print("\n✅ All requests sent! Refresh your Streamlit dashboard to see the complexity scores.")

if __name__ == "__main__":
    send_tests()
