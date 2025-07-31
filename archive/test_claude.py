#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
import anthropic

# Test API key loading
print(f"API Key loaded: {Config.ANTHROPIC_API_KEY[:10]}..." if Config.ANTHROPIC_API_KEY else "No API key")

# Test simple Claude request
try:
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[{"role": "user", "content": "Hello, just say 'test successful'"}]
    )
    print(f"Claude test successful: {response.content[0].text}")
except Exception as e:
    print(f"Claude test failed: {e}")