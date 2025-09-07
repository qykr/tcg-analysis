#!/usr/bin/env python3
"""
Test script to check which OpenRouter models are available
"""

import os
from dotenv import load_dotenv
from openrouter_client import OpenRouterClient

load_dotenv()

# Model options to test
MODEL_OPTIONS = [
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.1-70b-instruct", 
    "microsoft/phi-3-mini-128k-instruct",
    "google/gemini-flash-1.5",
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-haiku",
    "meta-llama/llama-3.2-3b-instruct"
]

def test_models():
    """Test which models are available on OpenRouter"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        print("Set it with: $env:OPENROUTER_API_KEY='your-api-key'")
        return
    
    print("🔍 Testing OpenRouter models...")
    print("=" * 50)
    
    client = OpenRouterClient(api_key)
    available_models = []
    
    for model in MODEL_OPTIONS:
        try:
            print(f"Testing {model}...", end=" ")
            response = client.chat(model, [{"role": "user", "content": "Hello"}], max_tokens=5)
            
            if response:
                print("✅ Available")
                available_models.append(model)
            else:
                print("❌ No response")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"✅ Available models: {len(available_models)}")
    for model in available_models:
        print(f"  - {model}")
    
    if available_models:
        print(f"\n🎯 Recommended model: {available_models[0]}")
    else:
        print("\n❌ No models available!")

if __name__ == "__main__":
    test_models()
