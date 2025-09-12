#!/usr/bin/env python3
"""
Resume generation from where it left off by checking existing responses.
"""

import asyncio
import json
import os
from get_reasoning_traces import ReasoningTraceGenerator

async def resume_generation():
    """Resume generation by skipping already completed problems."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        return
    
    # Check existing responses
    existing_responses = set()
    if os.path.exists('../data/responses.jsonl'):
        with open('../data/responses.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    response = json.loads(line.strip())
                    problem_id = response['problem_id']
                    response_type = response['type']
                    existing_responses.add((problem_id, response_type))
    
    print(f"Found {len(existing_responses)} existing responses")
    
    # Read all problems
    with open('../data/validation_problems.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert JSON structure to list of problems
    all_problems = []
    question_data = data.get('question', {})
    difficulty_data = data.get('difficulty', {})
    input_output_data = data.get('input_output', {})
    
    # Get all problem indices
    problem_indices = list(question_data.keys())
    
    for idx in problem_indices:
        problem = {
            'problem_id': idx,
            'question': question_data.get(idx, ''),
            'difficulty': difficulty_data.get(idx, ''),
            'input_output': input_output_data.get(idx, '')
        }
        all_problems.append(problem)
    
    # Filter out completed problems
    remaining_problems = []
    for problem in all_problems:
        problem_id = int(problem['problem_id'])
        naive_key = (problem_id, 'naive')
        reasoning_key = (problem_id, 'reasoning')
        
        if naive_key not in existing_responses or reasoning_key not in existing_responses:
            remaining_problems.append(problem)
    
    print(f"Remaining problems to process: {len(remaining_problems)}")
    
    if not remaining_problems:
        print("All problems already completed!")
        return
    
    # Initialize generator
    generator = ReasoningTraceGenerator(api_key)
    
    # Process remaining problems
    await generator.process_problems('../data/validation_problems.json', max_problems=len(remaining_problems))
    
    print("Resume completed!")

if __name__ == "__main__":
    asyncio.run(resume_generation())
