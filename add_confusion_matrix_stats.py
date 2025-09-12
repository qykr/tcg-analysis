#!/usr/bin/env python3
"""
Add confusion matrix statistics to existing response files that don't have them.
"""

import json
import sys
from pathlib import Path
from generation.confusion_matrix_utils import calculate_confusion_matrix_stats


def add_confusion_matrix_to_file(file_path: str):
    """Add confusion matrix statistics to a JSONL file."""
    print(f"Processing {file_path}...")
    
    # Read existing responses
    responses = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line.strip()))
    
    print(f"Found {len(responses)} responses")
    
    # Process each response
    updated_count = 0
    for response in responses:
        if 'confusion_matrix' not in response:
            # Calculate confusion matrix statistics
            expected_outputs = response.get('expected_outputs', [])
            generated_outputs = response.get('generated_outputs', [])
            
            if expected_outputs and generated_outputs:
                try:
                    confusion_matrix = calculate_confusion_matrix_stats(expected_outputs, generated_outputs)
                    response['confusion_matrix'] = confusion_matrix
                    updated_count += 1
                except Exception as e:
                    print(f"Error calculating confusion matrix for response {response.get('id', 'unknown')}: {e}")
    
    # Write updated responses back
    if updated_count > 0:
        with open(file_path, 'w') as f:
            for response in responses:
                f.write(json.dumps(response) + '\n')
        print(f"Updated {updated_count} responses with confusion matrix statistics")
    else:
        print("No responses needed updating")


def main():
    if len(sys.argv) != 2:
        print("Usage: python add_confusion_matrix_stats.py <file_path>")
        print("Example: python add_confusion_matrix_stats.py data/responses.jsonl")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"File {file_path} does not exist")
        sys.exit(1)
    
    add_confusion_matrix_to_file(file_path)


if __name__ == "__main__":
    main()
