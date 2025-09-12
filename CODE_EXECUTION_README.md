# Code Execution and Structured Outputs

This document describes the new features added to the LLM Response Analyzer for code execution and structured outputs.

## Features

### 1. Test Case Reasoning for Reasoner
The reasoner persona now:
- Takes the problem description (with sample inputs/outputs) and additional test inputs
- Reasons through each test input step-by-step like a human would on paper
- Uses OpenAI's structured outputs to return consistent JSON with reasoning and expected outputs
- Stores inputs, expected outputs, and generated outputs in the response

### 2. Code Execution for Naive Coder
The naive coder persona now:
- Generates Python code for the problem
- Extracts the code using regex (last Python code block)
- Executes the code on multiple test inputs using [SandboxFusion](https://github.com/bytedance/SandboxFusion)
- Stores inputs, expected outputs (N/A), and generated outputs in the response

## Setup

### Prerequisites
- Docker installed and running
- Python 3.8+
- Required Python packages (see requirements.txt)

### SandboxFusion Setup

1. **Automatic Setup** (Recommended):
   ```bash
   python setup_sandbox.py
   ```

2. **Manual Setup**:
   ```bash
   # Clone SandboxFusion
   git clone https://github.com/bytedance/SandboxFusion.git
   cd SandboxFusion
   
   # Build Docker images
   docker build -f ./scripts/Dockerfile.base -t code_sandbox:base .
   docker build -f ./scripts/Dockerfile.server -t code_sandbox:server .
   
   # Run the sandbox
   docker run -d --rm --privileged -p 8080:8080 --name sandbox-fusion code_sandbox:server make run-online
   ```

### Verify Setup
Check if the sandbox is running:
```bash
curl http://localhost:8080/health
```

## Usage

### Running Generation with New Features

1. **Test Generation**:
   ```bash
   cd generation
   python test_generation.py
   ```

2. **Full Generation**:
   ```bash
   python run_generation.py
   ```

### Response Format

#### Reasoner Response
```json
{
  "id": "r-1234567890.123",
  "problem_id": 1,
  "type": "reasoning",
  "trace": {
    "reasoning": "Step-by-step analysis for each test input...",
    "test_case_results": [
      {
        "input": "1",
        "expected_output": "1", 
        "reasoning": "First fibonacci number is 1"
      },
      {
        "input": "2",
        "expected_output": "1",
        "reasoning": "Second fibonacci number is 1"
      }
    ]
  },
  "inputs": ["1", "2", "3"],
  "expected_outputs": ["1", "1", "2"],
  "generated_outputs": ["1", "1", "2"]
}
```

#### Naive Coder Response
```json
{
  "id": "r-1234567890.124",
  "problem_id": 1,
  "type": "naive",
  "trace": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "inputs": ["1", "2", "3"],
  "expected_outputs": ["N/A", "N/A", "N/A"],
  "generated_outputs": ["1", "1", "2"]
}
```

## Configuration

### Sandbox URL
You can configure the sandbox URL by modifying the `ReasoningTraceGenerator` constructor:

```python
generator = ReasoningTraceGenerator(
    api_key=api_key,
    sandbox_url="http://your-sandbox-url:8080"
)
```

### Code Extraction
The code extraction uses regex to find the last Python code block in the format:
```python
# code here
```

## Troubleshooting

### Sandbox Issues
- **Sandbox not responding**: Check if Docker is running and the container is started
- **Permission denied**: Ensure Docker has proper permissions (may need `sudo` on Linux)
- **Port conflicts**: Change the port mapping if 8080 is already in use

### Code Execution Issues
- **No code extracted**: Check if the LLM response contains properly formatted Python code blocks
- **Execution timeout**: The sandbox has a 30-second timeout for code execution
- **Import errors**: Some Python packages may not be available in the sandbox

### Structured Output Issues
- **JSON parsing errors**: The system falls back to plain text if JSON parsing fails
- **Schema validation**: Ensure the LLM model supports structured outputs (GPT-4o, GPT-4o-mini)

## Security Notes

- Code execution happens in a Docker container for isolation
- The sandbox has resource limits and timeouts
- Only Python code is executed (other languages can be added to SandboxFusion)
- Network access may be limited in the sandbox environment

## References

- [OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/)
- [SandboxFusion GitHub](https://github.com/bytedance/SandboxFusion)
- [SandboxFusion Documentation](https://bytedance.github.io/SandboxFusion/)
