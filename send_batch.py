import json
import requests
import time

def send_prompts():
    url = "http://localhost:8000/chat"
    
    with open("prompts.json", "r") as f:
        prompts = json.load(f)
    
    print(f"🚀 Sending {len(prompts)} prompts to the gateway...")
    
    for item in prompts:
        payload = {
            "user_id": f"batch_user_{item['id']}",
            "text": item['prompt']
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"✅ Success [{item['id']}]: {item['prompt'][:50]}...")
            else:
                print(f"❌ Failed [{item['id']}]: {response.text}")
        except Exception as e:
            print(f"⚠️ Error: {e}")
        
        # Small delay to make it look smooth in the dashboard
        time.sleep(0.2)

    print("\n✨ Done! go to your browser and click 'Refresh Logs'.")

if __name__ == "__main__":
    send_prompts()
