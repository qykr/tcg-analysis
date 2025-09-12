#!/usr/bin/env python3
"""Test script for the new response format."""

import json
from prompts import generate_test_inputs, get_reasoner_prompt, get_naive_coder_prompt

def test_response_format():
    """Test the new response format."""
    print("🧪 Testing new response format...")
    
    # Test problem data
    problem_data = {
        'problem_id': '1',
        'question': 'Find the nth fibonacci number',
        'difficulty': 'EASY'
    }
    
    # Generate test inputs
    test_inputs = generate_test_inputs(problem_data, num_inputs=3)
    print(f"Generated test inputs: {test_inputs}")
    
    # Test reasoner prompt
    reasoner_prompt = get_reasoner_prompt(problem_data['question'], test_inputs)
    print(f"Reasoner prompt length: {len(reasoner_prompt)}")
    
    # Test naive coder prompt
    naive_prompt = get_naive_coder_prompt(problem_data['question'], "Standard input format")
    print(f"Naive coder prompt length: {len(naive_prompt)}")
    
    # Test response format
    sample_reasoner_response = {
        "id": "r-1234567890.123",
        "problem_id": 1,
        "type": "reasoning",
        "trace": {
            "reasoning": "Step-by-step analysis...",
            "test_case_results": [
                {"input": "1", "expected_output": "1", "reasoning": "First fibonacci number is 1"},
                {"input": "2", "expected_output": "1", "reasoning": "Second fibonacci number is 1"},
                {"input": "3", "expected_output": "2", "reasoning": "Third fibonacci number is 2"}
            ]
        },
        "inputs": test_inputs,
        "expected_outputs": ["1", "1", "2"],
        "generated_outputs": ["1", "1", "2"]
    }
    
    sample_naive_response = {
        "id": "r-1234567890.124",
        "problem_id": 1,
        "type": "naive",
        "trace": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        "inputs": test_inputs,
        "expected_outputs": ["N/A", "N/A", "N/A"],
        "generated_outputs": ["1", "1", "2"]
    }
    
    print("\n📋 Sample Reasoner Response:")
    print(json.dumps(sample_reasoner_response, indent=2))
    
    print("\n📋 Sample Naive Coder Response:")
    print(json.dumps(sample_naive_response, indent=2))
    
    print("\n✅ New response format test completed!")

if __name__ == "__main__":
    test_response_format()
