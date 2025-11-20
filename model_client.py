import os
import requests
import json

API_KEY = os.getenv("OPENAI_API_KEY")

def call_llm(prompt: str):
    """
    Stable version using Chat Completions with JSON response.
    Works on ALL OpenAI accounts.
    """

    if not API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a JSON generator. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        response.raise_for_status()
    except Exception as e:
        msg = f"HTTP {response.status_code}: {response.text}"
        raise RuntimeError(msg) from e

    data = response.json()

    # Extract JSON text output
    return data["choices"][0]["message"]["content"]
