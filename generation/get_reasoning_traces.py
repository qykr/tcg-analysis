#!/usr/bin/env python3
"""
Generate LLM reasoning traces for competitive programming problems.
Reads from validation_problems.json, generates naive coder and reasoner responses using OpenRouterClient,
and saves to responses.jsonl format.
"""

import asyncio
import json
import time
import os
from typing import Dict, List, Any
from tqdm import tqdm
from dotenv import load_dotenv
from lm_client import OpenRouterClient
from prompts import (
    get_naive_coder_prompt, 
    get_reasoner_prompt, 
    get_reasoner_schema,
    extract_python_code,
    generate_test_inputs,
    SandboxExecutor
)

# Load environment variables
load_dotenv()

class ReasoningTraceGenerator:
    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini", output_file: str = "responses.jsonl"):
        self.client = OpenRouterClient(api_key)
        self.model = model
        self.output_file = output_file
        self.results = []
        self.sandbox = SandboxExecutor()  # Use default local code runner
    
    def parse_input_output(self, problem) -> str:
        """Parse input/output from Problem object to extract input format description."""
        if hasattr(problem, 'sample_inputs') and problem.sample_inputs:
            return f"Input examples: {problem.sample_inputs[:3]}"  # Show first 3 examples
        return "Standard input format"
    
    def create_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Create messages for the LLM API."""
        return [
            {"role": "system", "content": "You are a helpful assistant that solves competitive programming problems."},
            {"role": "user", "content": prompt}
        ]
    
    def save_response(self, response: Dict[str, Any]):
        """Save a single response to JSONL file immediately."""
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(response) + '\n')
        self.results.append(response)
    
    async def generate_response(self, problem, persona_type: str) -> Dict[str, Any]:
        """Generate a single response for a problem."""
        problem_id = problem.id
        problem_name = problem.name
        question = problem.statement
        
        # Use sample inputs from the problem
        test_inputs = problem.sample_inputs[:3] if problem.sample_inputs else []
        test_outputs = problem.sample_outputs[:3] if problem.sample_outputs else []
        
        # Parse input format
        input_format = self.parse_input_output(problem)
        
        try:
            if persona_type == "reasoning":
                # Generate prompt with test inputs
                prompt = get_reasoner_prompt(question, test_inputs)
                messages = self.create_messages(prompt)
                
                # Get the full response
                full_response = await self.client.async_chat(
                    model=self.model,
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.7
                )
                
                # Extract JSON from the end of the response
                try:
                    # Look for JSON in code blocks first
                    import re
                    json_pattern = r'```json\s*(\{.*?\})\s*```'
                    json_match = re.search(json_pattern, full_response, re.DOTALL)
                    
                    if json_match:
                        json_part = json_match.group(1)
                        reasoning_text = full_response[:json_match.start()].strip()
                        parsed_output = json.loads(json_part)
                    else:
                        # Look for JSON at the end
                        json_start = full_response.rfind('{')
                        if json_start != -1:
                            json_part = full_response[json_start:]
                            reasoning_text = full_response[:json_start].strip()
                            parsed_output = json.loads(json_part)
                        else:
                            # No JSON found, try to extract from text
                            reasoning_text = full_response
                            
                            # Try to extract outputs from text patterns
                            import re
                            # Look for patterns like "Expected outputs: ['4', '-1', '-1']"
                            outputs_pattern = r'Expected outputs:\s*\[(.*?)\]'
                            outputs_match = re.search(outputs_pattern, full_response)
                            
                            if outputs_match:
                                try:
                                    outputs_str = outputs_match.group(1)
                                    # Parse the outputs string
                                    outputs = []
                                    for item in outputs_str.split(','):
                                        item = item.strip().strip("'\"")
                                        outputs.append(item)
                                    # Only take the first N outputs where N is the number of test inputs
                                    expected_outputs = outputs[:len(test_inputs)]
                                    generated_outputs = outputs[:len(test_inputs)]
                                except:
                                    expected_outputs = [str(output) for output in test_outputs]
                                    generated_outputs = ["N/A"] * len(test_inputs)
                            else:
                                expected_outputs = [str(output) for output in test_outputs]
                                generated_outputs = ["N/A"] * len(test_inputs)
                            parsed_output = None
                    
                    if parsed_output:
                        # Extract outputs
                        expected_outputs = []
                        generated_outputs = []
                        
                        if "outputs" in parsed_output:
                            outputs = parsed_output["outputs"]
                            for output in outputs:
                                expected_outputs.append(str(output))
                                generated_outputs.append(str(output))
                        else:
                            # Fallback: use actual expected outputs from the problem data
                            expected_outputs = [str(output) for output in test_outputs]
                            generated_outputs = ["N/A"] * len(test_inputs)
                        
                except json.JSONDecodeError:
                    # Fallback to plain text if JSON parsing fails
                    reasoning_text = full_response
                    expected_outputs = [str(output) for output in test_outputs]
                    generated_outputs = ["N/A"] * len(test_inputs)
                
                # Store the reasoning text directly as the trace
                structured_trace = reasoning_text
                
                # Create response object
                response = {
                    "id": f"r-{time.time()}",
                    "problem_id": int(problem_id),
                    "type": persona_type,
                    "trace": structured_trace,
                    "inputs": test_inputs,
                    "expected_outputs": expected_outputs,
                    "generated_outputs": generated_outputs
                }
                
            else:  # naive coder
                # Generate prompt with input format
                prompt = get_naive_coder_prompt(question, input_format)
                messages = self.create_messages(prompt)
                
                # Generate code
                trace = await self.client.async_chat(
                    model=self.model,
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                # Extract Python code from the response
                extracted_code = extract_python_code(trace)
                
                # Execute code with multiple test inputs
                execution_results = []
                generated_outputs = []
                if extracted_code:
                    try:
                        execution_results = self.sandbox.execute_code_multiple_inputs(extracted_code, test_inputs)
                        generated_outputs = [result["output"] for result in execution_results]
                    except Exception as e:
                        execution_results = [{"input": inp, "output": f"ERROR: {str(e)}", "success": False} for inp in test_inputs]
                        generated_outputs = [f"ERROR: {str(e)}"] * len(test_inputs)
                else:
                    execution_results = [{"input": inp, "output": "NO_CODE_EXTRACTED", "success": False} for inp in test_inputs]
                    generated_outputs = ["NO_CODE_EXTRACTED"] * len(test_inputs)
                
                # Create response object
                response = {
                    "id": f"r-{time.time()}",
                    "problem_id": int(problem_id),
                    "type": persona_type,
                    "trace": trace,
                    "inputs": test_inputs,
                    "expected_outputs": [str(output) for output in test_outputs],  # Use actual expected outputs
                    "generated_outputs": generated_outputs
                }
            
            # Save immediately to JSONL
            self.save_response(response)
            return response
            
        except Exception as e:
            print(f"Error generating response for problem {problem_id} ({persona_type}): {e}")
            return None
    
    async def process_problems(self, json_file: str, max_problems: int = 300):
        """Process problems from JSON and generate responses."""
        print(f"Reading problems from {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        
        # Convert JSON structure to list of problems
        problems = []
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
            problems.append(problem)
        
        # Limit to max_problems
        problems = problems[:max_problems]
        print(f"Processing {len(problems)} problems...")
        
        # Clear output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            pass  # Create empty file
        
        # Create tasks for all responses (2 per problem)
        tasks = []
        for problem in problems:
            # Add naive coder task
            tasks.append(self.generate_response(problem, "naive"))
            # Add reasoner task  
            tasks.append(self.generate_response(problem, "reasoning"))
        
        # Process with progress bar
        print(f"Generating {len(tasks)} responses...")
        results = []
        
        # Use asyncio.as_completed with tqdm
        with tqdm(total=len(tasks), desc="Generating responses") as pbar:
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:
                    results.append(result)
                pbar.update(1)
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
        
        print(f"Generated {len(results)} responses, saved to {self.output_file}")
    
    async def process_problems_from_list(self, problems):
        """Process problems from a list of Problem objects."""
        print(f"Processing {len(problems)} problems...")
        
        # Clear output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            pass  # Create empty file
        
        # Create tasks for all responses (2 per problem)
        tasks = []
        for problem in problems:
            # Add naive coder task
            tasks.append(self.generate_response(problem, "naive"))
            # Add reasoner task  
            tasks.append(self.generate_response(problem, "reasoning"))
        
        # Process with progress bar
        print(f"Generating {len(tasks)} responses...")
        results = []
        
        # Use asyncio.as_completed with tqdm
        with tqdm(total=len(tasks), desc="Generating responses") as pbar:
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:
                    results.append(result)
                pbar.update(1)
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
        
        print(f"Generated {len(results)} responses, saved to {self.output_file}")
    
    def save_results(self, output_file: str = "responses.jsonl"):
        """Save results to JSONL format (already saved line by line)."""
        print(f"Responses already saved to {self.output_file} during generation")
        print(f"Total responses: {len(self.results)}")

async def main():
    """Main function to run the trace generation."""
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your-key-here'")
        return
    
    # Initialize generator
    generator = ReasoningTraceGenerator(api_key)
    
    # Process problems
    await generator.process_problems('../data/validation_problems.json', max_problems=300)
    
    # Results already saved line by line
    generator.save_results()
    
    print("Done! Generated responses saved to responses.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
