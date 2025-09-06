# gets llm reasoning traces
# dump to responses.json

# in this format
# {
#   "id": "r-0001",
#   "problem_id": 2,
#   "problem_name": "nth-fibonacci-number1335",
#   "type": "solution",
#   "model": "gpt-4o",
#   "trace": "Explained dynamic programming approach...",
#   "difficulty": "EASY"
# }

# load from csv output.csv

import csv
import json
import requests
import time
import os
from dotenv import load_dotenv
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from openrouter_client import OpenRouterClient

# Load environment variables from .env file
load_dotenv()

# Increase CSV field size limit to handle large text fields
csv.field_size_limit(50_000_000)  # Increase to 1MB per field

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Use a cost-effective reasoning model
# Try these models in order of preference (first available will be used)
MODEL_OPTIONS = [
    "meta-llama/llama-3.1-8b-instruct",  # Free model with good reasoning capabilities
    "meta-llama/llama-3.1-70b-instruct",  # Larger, more capable model
    "microsoft/phi-3-mini-128k-instruct",  # Alternative free model
    "google/gemini-flash-1.5",  # Google's fast model
    "openai/gpt-3.5-turbo"  # Reliable fallback
]

MODEL = MODEL_OPTIONS[0]  # Start with the first option

# Thread-safe lock for file operations
file_lock = threading.Lock()

# Parallelization configuration
MAX_WORKERS = 5  # Number of concurrent threads (adjust based on API limits)
BATCH_SIZE = 20  # Problems per batch
BATCH_DELAY = 2  # Seconds to wait between batches

def find_available_model() -> str:
    """Find the first available model from the options list"""
    if not OPENROUTER_API_KEY:
        return MODEL_OPTIONS[0]  # Return first option if no API key
    
    for model in MODEL_OPTIONS:
        try:
            # Test the model with a simple request using OpenRouterClient
            openrouter_client = OpenRouterClient(OPENROUTER_API_KEY)
            test_messages = [{"role": "user", "content": "Hello"}]
            
            response = openrouter_client.chat(model, test_messages, max_tokens=10)
            
            if response:
                print(f"Using model: {model}")
                return model
                
        except Exception as e:
            print(f"Error testing model {model}: {str(e)}")
            continue
    
    print("No models available, using first option as fallback")
    return MODEL_OPTIONS[0]

def get_llm_reasoning_trace(problem_data: Dict[str, Any]) -> str:
    """Generate reasoning trace for a programming problem using OpenRouter API"""
    
    if not OPENROUTER_API_KEY:
        return "API key not provided - using placeholder trace"
    
    # Extract relevant problem information
    problem_id = problem_data.get('problem_id', 'Unknown')
    question = problem_data.get('question', 'No question provided')
    difficulty = problem_data.get('difficulty', 'Unknown')
    name = problem_data.get('name', 'Unknown problem')
    
    # Create a prompt for the LLM to generate reasoning traces
    prompt = f"""You are an expert programming tutor. Analyze this programming problem and provide a detailed reasoning trace showing your thought process for solving it.

Problem ID: {problem_id}
Problem Name: {name}
Difficulty: {difficulty}

Problem Description:
{question}

Please provide a step-by-step reasoning trace that includes:
1. Understanding the problem requirements
2. Identifying the key challenges
3. Considering different approaches
4. Explaining the optimal solution strategy
5. Discussing time and space complexity considerations

Keep your response concise but comprehensive, focusing on the reasoning process rather than just the final solution."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        openrouter_client = OpenRouterClient(OPENROUTER_API_KEY)
        response = openrouter_client.chat(MODEL, data['messages'])
        return response
        # response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
        # response.raise_for_status()

        
        # result = response.json()
        # trace = result['choices'][0]['message']['content']
        # return trace.strip()
        
    except Exception as e:
        print(f"Error generating trace for problem {problem_id}: {str(e)}")
        return f"Error generating trace: {str(e)}"

def process_single_problem(problem_data: Dict[str, Any], problem_index: int, total_problems: int) -> Dict[str, Any]:
    """Process a single problem and return the response entry"""
    problem_id = problem_data.get('problem_id')
    
    print(f"Processing problem {problem_index + 1}/{total_problems}: ID {problem_id}")
    
    # Generate reasoning trace
    trace = get_llm_reasoning_trace(problem_data)
    
    # Create response entry
    response_entry = {
        "id": f"r-{problem_index + 1:04d}",  # Will be updated later with actual count
        "problem_id": int(problem_id) if problem_id else 0,
        "problem_name": problem_data.get('name', 'unknown'),
        "type": "solution",
        "model": MODEL,
        "trace": trace,
        "difficulty": problem_data.get('difficulty', 'Unknown')
    }
    
    return response_entry

def save_responses_threadsafe(responses: List[Dict[str, Any]]):
    """Thread-safe function to save responses to file"""
    with file_lock:
        with open('responses.json', 'w') as f:
            json.dump(responses, f, indent=2)

def process_problems():
    """Process all problems from CSV and generate reasoning traces"""
    
    # Load existing responses if any
    existing_responses = []
    if os.path.exists('responses.json'):
        try:
            with open('responses.json', 'r') as f:
                existing_responses = json.load(f)
        except:
            existing_responses = []
    
    # Get existing problem IDs to avoid duplicates
    existing_problem_ids = {resp.get('problem_id') for resp in existing_responses}
    
    # Read CSV data with better error handling
    data = []
    try:
        with open('output.csv', mode='r', encoding='utf-8', errors='ignore') as infile:
            reader = csv.DictReader(infile)
            for i, row in enumerate(reader):
                try:
                    # Truncate very long fields to prevent memory issues
                    if 'question' in row and len(row['question']) > 10000:
                        row['question'] = row['question'][:10000] + "... [truncated]"
                    data.append(row)
                    
                    # Progress indicator for large files
                    if (i + 1) % 1000 == 0:
                        print(f"Loaded {i + 1} problems...")

                    if i > 5:
                        break
                        
                except Exception as e:
                    print(f"Error reading row {i + 1}: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []
    
    print(f"Successfully loaded {len(data)} problems from CSV")
    
    # Filter out already processed problems
    new_problems = []
    for i, problem_data in enumerate(data):
        problem_id = problem_data.get('problem_id')
        if problem_id not in existing_problem_ids:
            new_problems.append((problem_data, i))
        else:
            print(f"Skipping problem {problem_id} - already processed")
    
    print(f"Found {len(new_problems)} new problems to process")
    
    if not new_problems:
        print("No new problems to process!")
        return existing_responses
    
    # Process problems in parallel
    responses = existing_responses.copy()
    
    # Process in batches to avoid overwhelming the API
    total_batches = (len(new_problems) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(new_problems))
        batch_problems = new_problems[start_idx:end_idx]
        
        print(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_problems)} problems)")
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks in the batch
            future_to_problem = {
                executor.submit(
                    process_single_problem, 
                    problem_data, 
                    start_idx + i, 
                    len(data)
                ): (problem_data, start_idx + i) 
                for i, (problem_data, _) in enumerate(batch_problems)
            }
            
            # Collect results as they complete
            batch_responses = []
            for future in as_completed(future_to_problem):
                try:
                    response_entry = future.result()
                    batch_responses.append(response_entry)
                    print(f"Completed problem {response_entry['problem_id']}")
                except Exception as e:
                    problem_data, problem_index = future_to_problem[future]
                    print(f"Error processing problem {problem_data.get('problem_id')}: {str(e)}")
                    # Create error entry
                    error_entry = {
                        "id": f"r-{len(responses) + len(batch_responses) + 1:04d}",
                        "problem_id": int(problem_data.get('problem_id', 0)) if problem_data.get('problem_id') else 0,
                        "problem_name": problem_data.get('name', 'unknown'),
                        "type": "solution",
                        "model": MODEL,
                        "trace": f"Error processing: {str(e)}",
                        "difficulty": problem_data.get('difficulty', 'Unknown')
                    }
                    batch_responses.append(error_entry)
        
        # Add batch results to main responses
        responses.extend(batch_responses)
        
        # Save progress after each batch
        save_responses_threadsafe(responses)
        print(f"Completed batch {batch_num + 1}. Total responses: {len(responses)}")
        
        # Small delay between batches to be respectful to the API
        if batch_num < total_batches - 1:
            time.sleep(BATCH_DELAY)
    
    print(f"Completed! Generated {len(responses)} total responses")
    return responses

if __name__ == "__main__":
    # Check for API key
    if not OPENROUTER_API_KEY:
        print("Warning: OPENROUTER_API_KEY environment variable not set")
        print("Set it with: $env:OPENROUTER_API_KEY='your-api-key'")
        print("Continuing with placeholder traces...")
    else:
        # Find available model
        MODEL = find_available_model()
    
    # Process problems
    responses = process_problems()
    print(f"Generated {len(responses)} reasoning traces")

