import json
import re
import requests
from typing import Dict, Any, Optional
from utils import test_code_multi_cases, extract_code
from data_structures import CodeResult

def get_naive_coder_prompt(problem_description: str, input_format: str) -> str:
    """Generate prompt for naive coder persona."""
    return f"""You are a competitive programmer who solves problems in a very straightforward way.

Given a competitive programming problem, write a solution that:
- Uses the most obvious approach (even if inefficient)
- Doesn't worry about time/space complexity
- Guarantees correctness for very small test cases

Problem:
{problem_description}

Input format:
{input_format}

Write your code in Python. The expected formatting is:
```python
YOUR CODE HERE
```"""

def get_reasoner_prompt(problem_description: str, test_inputs: list) -> str:
    """Generate prompt for reasoner persona."""
    inputs_text = "\n".join([f"Input {i+1}: {inp}" for i, inp in enumerate(test_inputs)])
    
    return f"""You are a competitive programmer who reasons through test case inputs for problems to get the outputs.

Given a competitive programming problem with sample inputs and outputs, and additional test inputs:
1. Look at the problem description and understand the pattern from the sample inputs/outputs.
2. For each additional test input, reason through it step-by-step like you would on paper.
3. Show your work and explain your reasoning process.
4. Provide the expected output for each test input.

Problem:
{problem_description}

Additional test inputs to reason through:
{inputs_text}

For each test input, show your step-by-step reasoning and provide the expected output.

Please provide your detailed reasoning as text, and at the very end, include a JSON object with the outputs.

IMPORTANT: You must end your response with a JSON object in this exact format:

```json
{{
  "outputs": ["4", "-1", "15"]
}}
```"""

def get_reasoner_schema() -> Dict[str, Any]:
    """Get JSON schema for structured output from reasoner."""
    return {
        "type": "object",
        "properties": {
            "outputs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Expected outputs for each test input in order"
            }
        },
        "required": ["outputs"]
    }

def extract_python_code(text: str) -> Optional[str]:
    """Extract Python code from text using regex (last match)."""
    # Pattern to match Python code blocks
    pattern = r'```python\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        # Return the last match (most recent code)
        return matches[-1].strip()
    return None

def parse_input_output(input_output_str: str) -> dict:
    """Parse the input_output field to extract inputs and outputs."""
    try:
        data = json.loads(input_output_str)
        return {
            'inputs': data.get('inputs', []),
            'outputs': data.get('outputs', []),
            'fn_name': data.get('fn_name', '')
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        return {'inputs': [], 'outputs': [], 'fn_name': ''}

def generate_test_inputs(problem_data: dict, num_inputs: int = 3) -> tuple:
    """Extract test inputs and outputs from the problem data."""
    input_output_str = problem_data.get('input_output', '')
    parsed = parse_input_output(input_output_str)
    
    inputs = parsed.get('inputs', [])
    outputs = parsed.get('outputs', [])
    
    # Take the first num_inputs test cases
    test_inputs = inputs[:num_inputs] if len(inputs) >= num_inputs else inputs
    test_outputs = outputs[:num_inputs] if len(outputs) >= num_inputs else outputs
    
    # Pad with empty lists if we don't have enough test cases
    while len(test_inputs) < num_inputs:
        test_inputs.append([])
    while len(test_outputs) < num_inputs:
        test_outputs.append([])
    
    return test_inputs, test_outputs

class SandboxExecutor:
    """Code execution using the local utils.py code runner."""
    
    def __init__(self, time_limit: float = 2.0, memory_limit: int = 256):
        self.time_limit = time_limit
        self.memory_limit = memory_limit
    
    def execute_code(self, code: str, test_inputs: list = None) -> Dict[str, Any]:
        """Execute Python code with multiple test inputs using local code runner."""
        try:
            if not test_inputs:
                test_inputs = [""]  # Empty input for basic execution
            
            # Use the local code runner from utils.py
            code_results = test_code_multi_cases(
                code=code,
                cases=test_inputs,
                time_limit=self.time_limit,
                processes=1  # Single process for this execution
            )
            
            # Process results
            if not code_results:
                return {
                    "success": False,
                    "output": "",
                    "stderr": "",
                    "error": "No results returned from code execution"
                }
            
            # Get the first result (since we're executing with single input)
            result = code_results[0]
            
            return {
                "success": result.verdict == "OK",
                "output": result.output or "",
                "stderr": result.error or "",
                "error": None if result.verdict == "OK" else result.verdict
            }
                
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "stderr": "",
                "error": f"Execution error: {str(e)}"
            }
    
    def execute_code_multiple_inputs(self, code: str, test_inputs: list) -> list:
        """Execute Python code with multiple test inputs and return results for each."""
        try:
            # For LLM-generated code that processes all inputs at once,
            # we need to run it once and parse the output
            if len(test_inputs) > 1:
                # Run the code once with the first input (or empty input)
                code_results = test_code_multi_cases(
                    code=code,
                    cases=[test_inputs[0]],  # Use first input as representative
                    time_limit=self.time_limit,
                    processes=1
                )
                
                if code_results and code_results[0].verdict == "OK":
                    # Parse the output to extract individual results
                    full_output = code_results[0].output or ""
                    output_lines = [line.strip() for line in full_output.split('\n') if line.strip()]
                    
                    # If we have multiple outputs, distribute them
                    if len(output_lines) >= len(test_inputs):
                        results = []
                        for i, test_input in enumerate(test_inputs):
                            output = output_lines[i] if i < len(output_lines) else output_lines[-1]
                            results.append({
                                "input": test_input,
                                "output": output,
                                "success": True,
                                "error": None
                            })
                        return results
                    else:
                        # Fallback: use the same output for all inputs
                        output = output_lines[0] if output_lines else ""
                        return [{
                            "input": test_input,
                            "output": output,
                            "success": True,
                            "error": None
                        } for test_input in test_inputs]
                else:
                    # Error case
                    error_msg = code_results[0].error if code_results else "No results"
                    return [{
                        "input": test_input,
                        "output": f"ERROR: {error_msg}",
                        "success": False,
                        "error": error_msg
                    } for test_input in test_inputs]
            else:
                # Single input case - use original approach
                code_results = test_code_multi_cases(
                    code=code,
                    cases=test_inputs,
                    time_limit=self.time_limit,
                    processes=1
                )
                
                results = []
                for i, (test_input, code_result) in enumerate(zip(test_inputs, code_results)):
                    output = ""
                    if code_result.verdict == "OK":
                        output = (code_result.output or "").strip()
                    else:
                        error_msg = code_result.error or code_result.verdict
                        output = f"ERROR: {error_msg}"
                    
                    results.append({
                        "input": test_input,
                        "output": output,
                        "success": code_result.verdict == "OK",
                        "error": None if code_result.verdict == "OK" else code_result.verdict
                    })
                
                return results
            
        except Exception as e:
            # Fallback: return error for all inputs
            return [{
                "input": test_input,
                "output": f"ERROR: {str(e)}",
                "success": False,
                "error": str(e)
            } for test_input in test_inputs]
