#!/usr/bin/env python3
"""
Complete script to generate LLM reasoning traces and prepare for web app.
"""

import asyncio
import subprocess
import sys
import os
from dataset import get_val_problems, Config

async def main():
    print("🚀 Starting LLM reasoning trace generation...")
    
    # Check if API key is set
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your-key-here'")
        return
    
    try:
        # Load problems from TACO dataset
        print("📊 Loading problems from TACO dataset...")
        config = Config()
        problems = get_val_problems(config, num_problems=300)  # Load 300 validation problems
        print(f"✅ Loaded {len(problems)} problems from TACO dataset")
        
        # Run the trace generation
        print("📝 Generating reasoning traces...")
        from get_reasoning_traces import ReasoningTraceGenerator
        
        generator = ReasoningTraceGenerator(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            output_file='../data/responses.jsonl'
        )
        await generator.process_problems_from_list(problems)
        generator.save_results()
        
        # Convert to JSON format
        print("🔄 Converting to JSON format...")
        from convert_to_json import convert_jsonl_to_json
        convert_jsonl_to_json()
        
        print("✅ Done! Generated responses are ready for the web app.")
        print("📁 Files created:")
        print("  - responses.jsonl (raw output)")
        print("  - responses.json (for web app)")
        print("\n🌐 To view results, run: python3 server.py")
        print("   Then open: http://127.0.0.1:5173/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())
