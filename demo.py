# demo.py
from app.triage import route
import json

def run_demo():
    print("\n" + "="*60)
    print("  NEXUS-GATE LIVE ROUTING DEMO")
    print("="*60)
    print("Type 'exit' to quit.\n")

    while True:
        try:
            prompt = input("Enter prompt: ").strip()
            if not prompt or prompt.lower() == 'exit':
                break

            result = route(prompt)
            
            print(f"\n[ROUTED TO]: {result['model'].upper()}")
            print(f"[CONFIDENCE]: {result['confidence']:.1%}")
            print(f"[REASON]:     {result['reason']}")
            
            print("\n[FEATURE VALUES]:")
            for feat, val in result['features'].items():
                print(f" - {feat:<16}: {val:.3f}")
            print("-" * 60 + "\n")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    run_demo()
