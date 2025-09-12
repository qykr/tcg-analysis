#!/usr/bin/env python3
"""
Test script to generate a small number of responses for testing.
"""

import asyncio
import os
from get_reasoning_traces import ReasoningTraceGenerator
from dataset import get_val_problems, Config

async def test_generation():
    """Test with just 2 problems (4 responses total)."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        return
    
    print("🧪 Testing with 2 problems (4 responses total)...")
    
    # Load problems from TACO dataset
    config = Config()
    problems = get_val_problems(config, num_problems=2)
    print(f"Loaded {len(problems)} problems from TACO dataset")
    
    generator = ReasoningTraceGenerator(api_key, output_file='../data/test_responses.jsonl')
    await generator.process_problems_from_list(problems)
    generator.save_results()
    
    print("✅ Test completed! Check test_responses.jsonl")

if __name__ == "__main__":
    asyncio.run(test_generation())
