# test_api.py
from app.triage import route
from app.observability import log_request
import json

def test():
    prompt = "Explain quantum entanglement"
    print(f"Testing route() with prompt: {prompt}")
    try:
        routing = route(prompt)
        print(f"Features: {routing['features']}")
        
        print("Testing log_request()...")
        log_request(prompt, "Capable Model", routing["reason"], 100.5, False, routing["features"])
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
