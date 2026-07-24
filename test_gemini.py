"""Test script to verify Gemini API connectivity and key validity."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Try different models
models_to_try = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

api_key = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY: {api_key[:15]}...{api_key[-4:] if len(api_key) > 20 else ''}")

from google import genai

for model_name in models_to_try:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents="Respond with just the word: OK",
        )
        print(f"✅ {model_name}: {response.text}")
        break
    except Exception as e:
        print(f"❌ {model_name}: {type(e).__name__} - {str(e)[:80]}")