# LLM Reasoning Traces Generator

This script reads programming problems from `output.csv` and generates LLM reasoning traces using OpenRouter's API, then outputs them to `responses.json` in the specified format.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenRouter API key as an environment variable:
```bash
# Windows PowerShell
$env:OPENROUTER_API_KEY='your-api-key-here'

# Windows Command Prompt
set OPENROUTER_API_KEY=your-api-key-here

# Linux/Mac
export OPENROUTER_API_KEY='your-api-key-here'
```

## Usage

Run the script:
```bash
python test.py
```

## Features

- **Cost-effective**: Uses the free `meta-llama/llama-3.1-8b-instruct:free` model
- **Parallel processing**: Processes multiple problems concurrently (5 threads by default)
- **Resume capability**: Skips already processed problems if you restart
- **Progress saving**: Saves progress after each batch
- **Rate limiting**: Includes delays between batches to respect API limits
- **Error handling**: Continues processing even if individual requests fail
- **Configurable**: Easy to adjust parallelization settings at the top of the script

## Output Format

The script generates entries in `responses.json` with this structure:
```json
{
  "id": "r-0001",
  "problem_id": 2,
  "problem_name": "nth-fibonacci-number1335",
  "type": "solution",
  "model": "meta-llama/llama-3.1-8b-instruct:free",
  "trace": "Detailed reasoning trace...",
  "difficulty": "EASY"
}
```

## Configuration

You can adjust parallelization settings at the top of `test.py`:

```python
# Parallelization configuration
MAX_WORKERS = 5      # Number of concurrent threads (adjust based on API limits)
BATCH_SIZE = 20      # Problems per batch
BATCH_DELAY = 2      # Seconds to wait between batches
```

- **MAX_WORKERS**: Increase for faster processing (but respect API rate limits)
- **BATCH_SIZE**: Larger batches = fewer file saves, smaller batches = more frequent progress saves
- **BATCH_DELAY**: Longer delays = more respectful to API, shorter delays = faster processing

## Notes

- The script will process all problems in `output.csv`
- If `responses.json` already exists, it will append new entries
- Duplicate problem IDs are automatically skipped
- Each reasoning trace includes step-by-step problem analysis and solution strategy
- Parallel processing can be 3-5x faster than sequential processing
