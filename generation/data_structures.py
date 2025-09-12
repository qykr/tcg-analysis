from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

@dataclass
class Config:
    mapped_taco_path: str = '../data/mapped_taco.pkl'
    val_problems_path: str = '../data/val_problems.pkl'
    processes: int = 8

@dataclass
class Problem:
    """Represents a competitive programming problem with all its metadata"""
    id: str
    name: str
    statement: str
    sample_inputs: List[str]
    sample_outputs: List[str]
    solutions: List[str]
    time_limit: float = 2.0  # seconds
    memory_limit: int = 256  # MB

    def get_description(self) -> str:
        """
        Get the complete problem description formatted for LLM consumption
        Includes problem name, statement, and resource limits
        """
        description = f"Problem: {self.name}\n\n"
        description += f"Statement:\n{self.statement}\n\n"
        description += f"Time Limit: {self.time_limit} seconds\n"
        description += f"Memory Limit: {self.memory_limit} MB\n"
        
        return description

@dataclass
class CodeResult:
    """
    Result from executing a piece of code
    Contains execution metrics and verdict information
    """
    time: float  # seconds
    memory: float  # MB
    verdict: str  # "OK", "TLE", "MLE", "RTE", "WA"
    output: Optional[str] = None
    error: Optional[str] = None

@dataclass
class ConfusionMatrix:
    """
    Represents a confusion matrix with calculated metrics
    Used for evaluating validator performance
    """
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    
    @property
    def total_samples(self) -> int:
        """Total number of samples in the confusion matrix"""
        return self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
    
    @property
    def accuracy(self) -> float:
        """Accuracy: (TP + TN) / (TP + TN + FP + FN)"""
        if self.total_samples == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / self.total_samples
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def f1_score(self) -> float:
        """F1 Score: 2 * (precision * recall) / (precision + recall)"""
        denominator = self.precision + self.recall
        if denominator == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / denominator
    
    @property
    def specificity(self) -> float:
        """Specificity: TN / (TN + FP)"""
        denominator = self.true_negatives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_negatives / denominator
    
    def to_dict(self) -> dict:
        """Convert confusion matrix to dictionary format"""
        return {
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'specificity': self.specificity,
            'total_samples': self.total_samples
        }
    
    def __str__(self) -> str:
        """String representation of the confusion matrix"""
        return (f"ConfusionMatrix(TP={self.true_positives}, TN={self.true_negatives}, "
                f"FP={self.false_positives}, FN={self.false_negatives}, "
                f"Accuracy={self.accuracy:.3f}, Precision={self.precision:.3f}, "
                f"Recall={self.recall:.3f}, F1={self.f1_score:.3f})")
        
    def __add__(self, other: 'ConfusionMatrix') -> 'ConfusionMatrix':
        """Add two confusion matrices by summing their components"""
        return ConfusionMatrix(
            true_positives=self.true_positives + other.true_positives,
            true_negatives=self.true_negatives + other.true_negatives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives
        )