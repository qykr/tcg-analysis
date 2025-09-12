"""
Utilities for calculating confusion matrix statistics from expected vs generated outputs.
"""

from typing import List, Dict, Any
from data_structures import ConfusionMatrix


def calculate_confusion_matrix_stats(expected_outputs: List[str], generated_outputs: List[str]) -> Dict[str, Any]:
    """
    Calculate confusion matrix statistics by comparing expected vs generated outputs.
    
    For each test case:
    - True Positive (TP): Expected output matches generated output
    - False Positive (FP): Generated output is wrong but not empty/error
    - False Negative (FN): Expected output exists but generated is empty/error
    - True Negative (TN): Both expected and generated are empty/error (not applicable for most cases)
    
    Args:
        expected_outputs: List of expected output strings
        generated_outputs: List of generated output strings
        
    Returns:
        Dictionary containing confusion matrix statistics
    """
    if len(expected_outputs) != len(generated_outputs):
        raise ValueError("Expected and generated outputs must have the same length")
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0
    
    for expected, generated in zip(expected_outputs, generated_outputs):
        # Normalize outputs for comparison
        expected_norm = normalize_output(expected)
        generated_norm = normalize_output(generated)
        
        # Check if outputs are empty or error states
        expected_empty = is_empty_or_error(expected_norm)
        generated_empty = is_empty_or_error(generated_norm)
        
        if expected_empty and generated_empty:
            # Both are empty/error - True Negative
            true_negatives += 1
        elif expected_empty and not generated_empty:
            # Expected empty but generated something - False Positive
            false_positives += 1
        elif not expected_empty and generated_empty:
            # Expected something but generated empty - False Negative
            false_negatives += 1
        elif expected_norm == generated_norm:
            # Both match - True Positive
            true_positives += 1
        else:
            # Both non-empty but different - False Positive
            false_positives += 1
    
    # Create confusion matrix object
    cm = ConfusionMatrix(
        true_positives=true_positives,
        true_negatives=true_negatives,
        false_positives=false_positives,
        false_negatives=false_negatives
    )
    
    return cm.to_dict()


def normalize_output(output: str) -> str:
    """
    Normalize output string for comparison.
    - Strip whitespace
    - Convert to lowercase
    - Handle common variations
    """
    if not output:
        return ""
    
    # Strip whitespace and convert to lowercase
    normalized = str(output).strip().lower()
    
    # Handle common variations
    if normalized in ["n/a", "na", "none", "null", "error", "no_code_extracted"]:
        return ""
    
    return normalized


def is_empty_or_error(output: str) -> bool:
    """
    Check if output is considered empty or an error state.
    """
    normalized = normalize_output(output)
    return normalized == ""


def calculate_aggregate_stats(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate confusion matrix statistics across all responses.
    
    Args:
        responses: List of response dictionaries with confusion_matrix field
        
    Returns:
        Dictionary containing aggregate statistics
    """
    total_tp = 0
    total_tn = 0
    total_fp = 0
    total_fn = 0
    
    for response in responses:
        if 'confusion_matrix' in response:
            cm = response['confusion_matrix']
            total_tp += cm.get('true_positives', 0)
            total_tn += cm.get('true_negatives', 0)
            total_fp += cm.get('false_positives', 0)
            total_fn += cm.get('false_negatives', 0)
    
    # Create aggregate confusion matrix
    aggregate_cm = ConfusionMatrix(
        true_positives=total_tp,
        true_negatives=total_tn,
        false_positives=total_fp,
        false_negatives=total_fn
    )
    
    return aggregate_cm.to_dict()
