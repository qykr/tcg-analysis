#!/usr/bin/env python3
"""
Summarize performance statistics across all responses in a JSONL file.
"""

import json
import sys
from pathlib import Path
from generation.confusion_matrix_utils import calculate_aggregate_stats


def summarize_performance(file_path: str):
    """Summarize performance statistics from a JSONL file."""
    print(f"Analyzing {file_path}...")
    
    # Read responses
    responses = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line.strip()))
    
    print(f"Found {len(responses)} responses")
    
    # Separate by type
    naive_responses = [r for r in responses if r.get('type') == 'naive']
    reasoning_responses = [r for r in responses if r.get('type') == 'reasoning']
    
    print(f"  - Naive: {len(naive_responses)}")
    print(f"  - Reasoning: {len(reasoning_responses)}")
    print()
    
    # Calculate aggregate statistics
    if naive_responses:
        print("=== NAIVE CODER PERFORMANCE ===")
        naive_stats = calculate_aggregate_stats(naive_responses)
        print(f"Accuracy: {naive_stats['accuracy']:.3f}")
        print(f"Precision: {naive_stats['precision']:.3f}")
        print(f"Recall: {naive_stats['recall']:.3f}")
        print(f"F1 Score: {naive_stats['f1_score']:.3f}")
        print(f"Specificity: {naive_stats['specificity']:.3f}")
        print(f"Total Samples: {naive_stats['total_samples']}")
        print(f"True Positives: {naive_stats['true_positives']}")
        print(f"False Positives: {naive_stats['false_positives']}")
        print(f"False Negatives: {naive_stats['false_negatives']}")
        print(f"True Negatives: {naive_stats['true_negatives']}")
        print()
    
    if reasoning_responses:
        print("=== REASONING PERFORMANCE ===")
        reasoning_stats = calculate_aggregate_stats(reasoning_responses)
        print(f"Accuracy: {reasoning_stats['accuracy']:.3f}")
        print(f"Precision: {reasoning_stats['precision']:.3f}")
        print(f"Recall: {reasoning_stats['recall']:.3f}")
        print(f"F1 Score: {reasoning_stats['f1_score']:.3f}")
        print(f"Specificity: {reasoning_stats['specificity']:.3f}")
        print(f"Total Samples: {reasoning_stats['total_samples']}")
        print(f"True Positives: {reasoning_stats['true_positives']}")
        print(f"False Positives: {reasoning_stats['false_positives']}")
        print(f"False Negatives: {reasoning_stats['false_negatives']}")
        print(f"True Negatives: {reasoning_stats['true_negatives']}")
        print()
    
    # Overall statistics
    if responses:
        print("=== OVERALL PERFORMANCE ===")
        overall_stats = calculate_aggregate_stats(responses)
        print(f"Accuracy: {overall_stats['accuracy']:.3f}")
        print(f"Precision: {overall_stats['precision']:.3f}")
        print(f"Recall: {overall_stats['recall']:.3f}")
        print(f"F1 Score: {overall_stats['f1_score']:.3f}")
        print(f"Specificity: {overall_stats['specificity']:.3f}")
        print(f"Total Samples: {overall_stats['total_samples']}")
        print(f"True Positives: {overall_stats['true_positives']}")
        print(f"False Positives: {overall_stats['false_positives']}")
        print(f"False Negatives: {overall_stats['false_negatives']}")
        print(f"True Negatives: {overall_stats['true_negatives']}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python summarize_performance.py <file_path>")
        print("Example: python summarize_performance.py data/test_responses.jsonl")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"File {file_path} does not exist")
        sys.exit(1)
    
    summarize_performance(file_path)


if __name__ == "__main__":
    main()
