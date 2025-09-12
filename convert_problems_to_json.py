#!/usr/bin/env python3
"""
Convert Problem dataclass from pickle to JSON format for webapp.
"""

import pickle
import json
from pathlib import Path
import sys
sys.path.append('generation')
from data_structures import Problem


def convert_problems_to_json():
    """Convert problems from pickle to JSON format."""
    pickle_path = Path('data/val_problems.pkl')
    json_path = Path('data/validation_problems.json')
    
    if not pickle_path.exists():
        print(f"Pickle file {pickle_path} not found")
        return
    
    # Load problems from pickle
    with open(pickle_path, 'rb') as f:
        problems = pickle.load(f)
    
    print(f"Loaded {len(problems)} problems from pickle")
    
    # Convert to webapp format
    webapp_problems = []
    for i, problem in enumerate(problems):
        if isinstance(problem, Problem):
            webapp_problem = {
                'problem_id': str(problem.id),
                'name': problem.name,
                'question': problem.statement,
                'difficulty': problem.difficulty,  # We don't have difficulty in Problem dataclass
                'tags': [],  # We don't have tags in Problem dataclass
                'url': '',  # We don't have URL in Problem dataclass
                'time_limit': str(problem.time_limit),
                'memory_limit': str(problem.memory_limit),
                'sample_inputs': problem.sample_inputs,
                'sample_outputs': problem.sample_outputs,
            }
            webapp_problems.append(webapp_problem)
        else:
            print(f"Warning: Problem {i} is not a Problem dataclass: {type(problem)}")
    
    # Save as JSON
    with open(json_path, 'w') as f:
        json.dump(webapp_problems, f, indent=2)
    
    print(f"Converted {len(webapp_problems)} problems to {json_path}")


if __name__ == "__main__":
    convert_problems_to_json()
