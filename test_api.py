import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE = "https://api.openai.com/v1"

payload = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello! This is a test."}]
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

r = requests.post(f"{BASE}/chat/completions", json=payload, headers=headers)
print("Status:", r.status_code)
print(r.json())
