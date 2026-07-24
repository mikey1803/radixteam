"""Test script to verify OpenAI API connectivity and key validity."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")


async def test_openai_connection():
    """Test OpenAI API connection and key validity."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    print("=" * 60)
    print("OpenAI API Connection Test")
    print("=" * 60)
    
    if not api_key:
        print("❌ OPENAI_API_KEY is not set in .env file")
        return False
    
    print(f"✓ API Key found: {api_key[:15]}...{api_key[-4:]}")
    print(f"✓ Model: {model}")
    print(f"✓ Base URL: {base_url or 'https://api.openai.com/v1 (default)'}")
    print()
    
    try:
        from openai import AsyncOpenAI
        
        client_kwargs = {"api_key": api_key.strip()}
        if base_url:
            client_kwargs["base_url"] = base_url.strip()
        
        client = AsyncOpenAI(**client_kwargs)
        
        print("Testing API connection with a simple request...")
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=20,
        )
        
        result = response.choices[0].message.content
        print(f"✅ SUCCESS! API Response: {result}")
        print()
        print("=" * 60)
        print("Your OpenAI API is working correctly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print()
        print("=" * 60)
        print("Common fixes:")
        print("1. Check if your API key is valid and not expired")
        print("2. Verify you have billing set up on your OpenAI account")
        print("3. Check if the model name is correct")
        print("4. Ensure network connectivity to OpenAI servers")
        print("=" * 60)
        return False


if __name__ == "__main__":
    asyncio.run(test_openai_connection())
