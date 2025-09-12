from datasets import load_dataset
from typing import Optional, List
import logging
import json
import pickle
import os
import asyncio
import tqdm
import sys
from data_structures import Problem, Config

# set maximum integer string digits to avoid overflow issues
sys.set_int_max_str_digits(0)

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_json(file_path: str, default: dict = {}):
    """
    Load JSON data from file with error handling
    Returns default value if file doesn't exist or is invalid
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return default

def map_taco_problem(problem: dict, idx: int) -> Problem:
    """
    Convert a TACO dataset problem dictionary to our Problem data structure
    Extracts input/output pairs and other metadata from the TACO format
    """
    in_out = json.loads(problem["input_output"])
    
    # Parse time limit (e.g., "2.0 seconds" -> 2.0)
    time_limit = 2.0  # default
    if problem.get("time_limit"):
        try:
            time_limit = float(problem["time_limit"].split()[0])
        except (ValueError, IndexError):
            time_limit = 2.0
    
    # Parse memory limit (e.g., "256.0 megabytes" -> 256)
    memory_limit = 256  # default
    if problem.get("memory_limit"):
        try:
            memory_limit = int(float(problem["memory_limit"].split()[0]))
        except (ValueError, IndexError):
            memory_limit = 256
    
    return Problem(
        id = str(idx + 1),
        name = problem.get("name") or f"Problem {idx + 1}",
        statement = problem["question"],
        sample_inputs = in_out["inputs"],
        sample_outputs = in_out["outputs"],
        difficulty = problem.get("difficulty") or "UNKNOWN_DIFFICULTY",
        solutions = eval(problem["solutions"]) if problem["solutions"] else [],
        time_limit = time_limit,
        memory_limit = memory_limit
    )

def get_mapped_taco(config: Config, split="train", remove_interactive=True) -> List[Problem]:
    """
    Load and process the TACO dataset, converting it to our Problem format
    Filters out interactive problems if requested and caches the processed data
    """
    def map_full():
        """Process the full dataset and save to cache"""
        logging.info(f"No cached TACO mapping found. Creating a new one at {config.mapped_taco_path}")
        dataset_mapped = []
        taco_ids_to_index = {}
        dataset = load_dataset("BAAI/TACO", split=split)
        # keywords to identify interactive problems that should be filtered out
        keywords = [
            "interact with", "query the judge", "ask the judge", "exchange of data",
            "communicate back and forth", "judge responds", "your program will wait",
            "flush(", "adaptive input", "adversarial", "guess the number", "interactive",
            "Interactive", "Interaction", "interaction"
        ]
        # process each problem in the dataset
        for i, item in enumerate(tqdm.tqdm(dataset, desc="Mapping TACO dataset")):
            # skip interactive problems if filtering is enabled
            if remove_interactive and any(key in item["question"] for key in keywords):
                continue
            problem = map_taco_problem(item, i)
            dataset_mapped.append(problem)
            
        # save processed dataset to cache file
        pickle.dump(dataset_mapped, open(config.mapped_taco_path, "wb"))
        return dataset_mapped
    
    # try to load from cache first, fall back to processing if cache is corrupted
    if os.path.exists(config.mapped_taco_path):
        with open(config.mapped_taco_path, "rb") as f:
            try:
                logging.info(f"Loading saved TACO mapping in path {config.mapped_taco_path}")
                return pickle.load(f)
            except:
                return map_full()
    else:
        # create directory and process dataset if cache doesn't exist
        os.makedirs(os.path.dirname(config.mapped_taco_path), exist_ok=True)
        logging.info(f"File path {config.mapped_taco_path} created")
        return map_full()
    
def get_val_problems(config: Config, num_problems: int = 300) -> List[Problem]:
    """
    Filter TACO problems based on the given configuration
    """
    def filter_problems():
        """Process and filter problems, then save to cache"""
        logging.info(f"No cached validation problems found. Creating a new one at {config.val_problems_path}")
        problems = get_mapped_taco(config)
        problems_filtered = []
        unique_difficulties = set()
        
        # First pass: collect unique difficulties and filter out invalid problems
        for problem in tqdm.tqdm(problems, desc="Getting problem data"):
            if hasattr(problem, 'difficulty') and problem.difficulty == 'UNKNOWN_DIFFICULTY':
                continue
            if hasattr(problem, 'input_output') and problem.input_output == None:
                continue
            
            # Only add valid difficulties to unique set
            if hasattr(problem, 'difficulty') and problem.difficulty != 'UNKNOWN_DIFFICULTY':
                unique_difficulties.add(problem.difficulty)
        
        # Calculate distribution across difficulties
        num_per_difficulty = num_problems // len(unique_difficulties) if unique_difficulties else num_problems
        difficulty_count = {difficulty: 0 for difficulty in unique_difficulties}
            
        # Second pass: select problems based on difficulty distribution
        for problem in tqdm.tqdm(problems, desc="Filtering validation problems"):
            # Stop if we have enough problems
            if len(problems_filtered) >= num_problems:
                break
                
            # Skip problems with UNKNOWN_DIFFICULTY
            if hasattr(problem, 'difficulty') and problem.difficulty == 'UNKNOWN_DIFFICULTY':
                continue
                
            if hasattr(problem, 'difficulty') and problem.difficulty in difficulty_count:
                if difficulty_count[problem.difficulty] >= num_per_difficulty:
                    continue
                difficulty_count[problem.difficulty] += 1
            elif not hasattr(problem, 'difficulty'):
                # If no difficulty info, just add up to the limit
                if len(problems_filtered) >= num_problems:
                    continue
            
            problems_filtered.append(problem)
            
        # Save to cache
        print(f"Number of problems filtered: {len(problems_filtered)}")
        pickle.dump(problems_filtered, open(config.val_problems_path, "wb"))
        
        # Automatically convert to JSON for webapp
        convert_problems_to_json(problems_filtered)
        
        return problems_filtered
    
    # Try to load from cache first, fall back to processing if cache is corrupted
    if os.path.exists(config.val_problems_path):
        with open(config.val_problems_path, "rb") as f:
            try:
                logging.info(f"Loading saved validation problems from {config.val_problems_path}")
                cached_problems = pickle.load(f)
                # Check if we have enough problems
                if len(cached_problems) >= num_problems:
                    return cached_problems[:num_problems]
                else:
                    logging.info(f"Cached problems ({len(cached_problems)}) less than requested ({num_problems}), reprocessing...")
                    return filter_problems()
            except Exception as e:
                logging.warning(f"Failed to load cached validation problems: {e}, reprocessing...")
                return filter_problems()
    else:
        # Create directory and process dataset if cache doesn't exist
        os.makedirs(os.path.dirname(config.val_problems_path), exist_ok=True)
        logging.info(f"File path {config.val_problems_path} created")
        return filter_problems()

def convert_problems_to_json(problems: List[Problem], json_path: str = None) -> str:
    """
    Convert Problem dataclass objects to JSON format for webapp.
    Returns the path to the created JSON file.
    """
    if json_path is None:
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'validation_problems.json')
    
    # Convert to webapp format
    webapp_problems = []
    for i, problem in enumerate(problems):
        if isinstance(problem, Problem):
            webapp_problem = {
                'problem_id': str(problem.id),
                'name': problem.name,
                'question': problem.statement,
                'difficulty': problem.difficulty,
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
    return json_path
    
if __name__ == "__main__":
    config = Config()
    problems = get_val_problems(config, num_problems=300)
    print(f"Loaded {len(problems)} problems from TACO dataset")
    
    # Automatically convert to JSON for webapp
    convert_problems_to_json(problems)