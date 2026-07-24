"""Debug script to test Gemini API connectivity."""
import os
import json
import urllib.request
import urllib.error
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

print(f"Model: {model}")
print(f"Key starts with: {key[:15] if key else 'NOT SET'}...")

# Test 1: Simple text request
print("\n--- Test 1: Simple request ---")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
payload = {
    "contents": [{"parts": [{"text": "Say hello in JSON: {\"response\": \"hello\"}"}]}],
    "generationConfig": {"temperature": 0.0}
}

body = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        print("SUCCESS!")
        print(json.dumps(data, indent=2)[:800])
except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP Error {e.code}: {error_body[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:500]}")

# Test 2: With response_mime_type
print("\n--- Test 2: With response_mime_type ---")
payload2 = {
    "contents": [{"parts": [{"text": "Return JSON: {\"status\": \"ok\"}"}]}],
    "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"}
}
body2 = json.dumps(payload2).encode("utf-8")
req2 = urllib.request.Request(url, data=body2, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req2, timeout=30) as resp:
        data = json.loads(resp.read())
        print("SUCCESS!")
        print(json.dumps(data, indent=2)[:800])
except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP Error {e.code}: {error_body[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:500]}")