#!/usr/bin/env python3
"""
Test script to generate a small number of responses for testing.
"""

import asyncio
import os
import argparse
from get_reasoning_traces import ReasoningTraceGenerator
from dataset import get_val_problems, Config

async def process_with_semaphore(semaphore, generator, problem, persona_type, progress_callback):
    """Process a single response with semaphore control."""
    async with semaphore:
        try:
            result = await generator.generate_response(problem, persona_type)
            progress_callback()
            return result
        except Exception as e:
            print(f"Error processing {persona_type} for problem {problem.id}: {e}")
            return None

async def test_generation(num_problems=2, disable_reasoning=False, disable_naive=False, max_concurrent=5, start_id=None):
    """Test with specified number of problems and generation types."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        return
    
    if disable_reasoning and disable_naive:
        print("Error: Cannot disable both reasoning and naive generation")
        return
    
    # Load problems from TACO dataset
    config = Config()
    all_problems = get_val_problems(config, num_problems=1000)  # Load more to filter from
    
    # Filter problems by start_id if specified
    if start_id is not None:
        # Convert start_id to string for comparison
        start_id_str = str(start_id)
        problems = [p for p in all_problems if p.id >= start_id_str]
        print(f"Filtered to {len(problems)} problems with ID >= {start_id_str}")
    else:
        problems = all_problems
    
    # Take only the requested number of problems
    problems = problems[:num_problems]
    
    # Calculate expected number of responses
    expected_responses = 0
    if not disable_naive:
        expected_responses += len(problems)
    if not disable_reasoning:
        expected_responses += len(problems)
    
    print(f"🧪 Testing with {len(problems)} problems ({expected_responses} responses total)...")
    print(f"   - Max concurrent requests: {max_concurrent}")
    if start_id is not None:
        print(f"   - Starting from problem ID: {start_id}")
    if disable_reasoning:
        print("   - Reasoning generation disabled")
    if disable_naive:
        print("   - Naive generation disabled")
    
    print(f"Loaded {len(problems)} problems from TACO dataset")
    
    generator = ReasoningTraceGenerator(api_key, output_file='../data/test_responses.jsonl')
    
    # Create semaphore for controlled concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Track progress
    completed_count = 0
    def progress_callback():
        nonlocal completed_count
        completed_count += 1
        print(f"Completed {completed_count}/{expected_responses} responses...")
    
    # Create tasks for all responses
    tasks = []
    for problem in problems:
        if not disable_naive:
            task = process_with_semaphore(semaphore, generator, problem, "naive", progress_callback)
            tasks.append(task)
        if not disable_reasoning:
            task = process_with_semaphore(semaphore, generator, problem, "reasoning", progress_callback)
            tasks.append(task)
    
    # Process all tasks concurrently
    print(f"Generating {len(tasks)} responses with controlled concurrency...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and None results
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    
    generator.save_results()
    print(f"✅ Test completed! Generated {len(valid_results)} valid responses. Check test_responses.jsonl")

def main():
    parser = argparse.ArgumentParser(description='Test LLM reasoning trace generation')
    parser.add_argument('--num-problems', type=int, default=2, 
                       help='Number of problems to test with (default: 2)')
    parser.add_argument('--disable-reasoning', action='store_true',
                       help='Disable reasoning trace generation')
    parser.add_argument('--disable-naive', action='store_true',
                       help='Disable naive coder generation')
    parser.add_argument('--max-concurrent', type=int, default=5,
                       help='Maximum number of concurrent requests (default: 5)')
    parser.add_argument('--start-id', type=str, default=None,
                       help='Minimum problem ID to start generation from (default: None)')
    
    args = parser.parse_args()
    
    asyncio.run(test_generation(
        num_problems=args.num_problems,
        disable_reasoning=args.disable_reasoning,
        disable_naive=args.disable_naive,
        max_concurrent=args.max_concurrent,
        start_id=args.start_id
    ))

if __name__ == "__main__":
    main()
