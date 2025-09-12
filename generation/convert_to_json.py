#!/usr/bin/env python3
"""
Convert responses.jsonl to responses.json for the web app.
"""

import json

def convert_jsonl_to_json(input_file: str = "../data/responses.jsonl", output_file: str = "../data/responses.json"):
    """Convert JSONL file to JSON array."""
    responses = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line.strip()))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(responses, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(responses)} responses from {input_file} to {output_file}")

if __name__ == "__main__":
    convert_jsonl_to_json()
