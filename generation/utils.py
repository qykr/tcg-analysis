import re
import time
import builtins
import json
import io
import sys
import multiprocessing
import resource
import ast
import asyncio
from functools import wraps
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from data_structures import CodeResult

# import libraries to make available for the test code that is generated
import math
import random
import numpy as np

# default globals dictionary for code execution environment
default_globals = {
    "__builtins__": __builtins__,
    "math": math,
    "random": random,
    "np": np,
    "sys": sys
}

# Copied from LCB (livecodebench)
def clean_if_main(code: str) -> str:
    """
    Remove the if __name__ == '__main__' block from code and extract its contents
    This allows the main block code to be executed directly
    """
    try:
        astree = ast.parse(code)
        last_block = astree.body[-1]
        if isinstance(last_block, ast.If):
            condition = last_block.test
            if ast.unparse(condition).strip() == "__name__ == '__main__'":
                code = (
                    ast.unparse(astree.body[:-1]) + "\n" + ast.unparse(last_block.body)  # type: ignore
                )
    except:
        pass

    return code

def extract_code(text: str, language: str = "python") -> Optional[str]:
    """
    Extract markdown code blocks from text given a language
    Returns the last code block found, or None if none found
    """
    compiled = re.findall(f"```{language}(.*?)```", text, re.DOTALL)
    if len(compiled) > 0:
        return clean_if_main(compiled[-1].strip())
    else:
        return None

def extract_configuration(text: str) -> List[str]:
    """
    Extract configuration commands from markdown text
    Looks for patterns like **Configuration:** `command`
    """
    return re.findall(r"\*\*Configuration:\*\* `(.*?)`", text, re.DOTALL)

# TODO: Fix ts
def reliability_guard(memory_limit: float = 256):
    """
    Set resource limits for memory usage to prevent system overload
    Currently disabled but can be used to enforce memory limits
    """
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    memory_limit_bytes = int(memory_limit * 1024 * 1024)  # in bytes

    if memory_limit_bytes > hard:
        memory_limit_bytes = hard  # Cap to avoid ValueError
        
    print(memory_limit_bytes, hard)
        
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
    resource.setrlimit(resource.RLIMIT_DATA, (memory_limit_bytes, memory_limit_bytes))
    if not sys.platform == "darwin":
       resource.setrlimit(resource.RLIMIT_STACK, (memory_limit_bytes, memory_limit_bytes))

def run_code(
    code: str,
    case_input: str,
    output_queue: multiprocessing.Queue,
    memory_limit: float = 256
):
    """
    Run a piece of code with given inputs and capture the outputs
    This function is designed to run in a separate process for isolation
    """
    
    #reliability_guard(memory_limit)
    
    def get_peak_memory_mb():
        """Get peak memory usage in MB"""
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == 'darwin': # darwin is Mac OS X
            return usage / (1024 * 1024)  # Convert bytes -> MB
        else:
            return usage / 1024 # Convert KB -> MB  
            
    start = time.time()

    # mock input by redirecting stdin
    input_stream = io.StringIO(case_input)
    sys.stdin = input_stream
    builtins.input = lambda: input_stream.readline().rstrip('\n')  # Optional override

    # capture output by redirecting stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        exec(code, default_globals)
    except Exception as e:
        # check if memory limit was exceeded
        if (get_peak_memory_mb() >= memory_limit):
            output_queue.put(CodeResult(
                time=time.time() - start,
                memory=get_peak_memory_mb(),
                verdict="Memory Limit Error",
                error=str(e)
            ), False)
            return
        
        # handle runtime errors
        output_queue.put(CodeResult(
            time=time.time() - start,
            memory=get_peak_memory_mb(),
            verdict="Runtime Error",
            error=str(e)
        ), False)
        return
    finally:
        # restore stdout
        sys.stdout = sys.__stdout__

    # success case
    result = CodeResult(
        output=buf.getvalue(),
        time=time.time() - start,
        memory=get_peak_memory_mb(),
        verdict="OK"
    )
    output_queue.put(result, False)
    return

def _run_code_wrapper(args: Tuple[str, str, float]) -> CodeResult:
    """
    Wrapper function for running code that can be used with ProcessPoolExecutor
    Handles process creation, timeout, and result extraction
    """
    code, case, time_limit = args

    # Create a manager and queue for this specific execution
    manager = multiprocessing.Manager()
    output_queue = manager.Queue()

    # run the code in a separate process for isolation
    p = multiprocessing.Process(target=run_code, args=(code, case, output_queue))
    p.start()
    p.join(timeout=time_limit)

    # handle timeout case
    if p.is_alive():
        p.terminate()
        return CodeResult(
            time=time_limit,
            memory=0,
            verdict="Time Limit Error"
        )
    else:
        # extract result from queue
        try:
            return output_queue.get(timeout=1)
        except Exception as e:
            return CodeResult(
                time=0,
                memory=0,
                verdict="Runtime Error",
                error=str(e)
            )

def test_code_single_case(code: str, case: str, time_limit: float = 2) -> CodeResult:
    """Single case execution - kept for backward compatibility"""
    return _run_code_wrapper((code, case, time_limit))

def test_code_multi_cases(
    code: str,
    cases: List[str],
    time_limit: float = 2,
    processes = 8,
    max_workers: Optional[int] = None
) -> List[CodeResult]:
    """
    Execute multiple test cases using a process pool for better efficiency
    Runs each case in parallel using separate processes
    """
    if not cases:
        return []

    # Prepare arguments for each case
    args_list = [(code, case, time_limit) for case in cases]

    # Use ProcessPoolExecutor for parallel execution
    if max_workers is None:
        max_workers = min(len(cases), processes)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_run_code_wrapper, args_list))

    return results

async def test_code_multi_cases_async(
    code: str,
    cases: List[str],
    time_limit: float = 2,
    processes = 8,
    max_workers: Optional[int] = None
) -> List[CodeResult]:
    """
    Execute multiple test cases using a process pool asynchronously
    Non-blocking version of test_code_multi_cases for use in async contexts
    """
    if not cases:
        return []

    # prepare arguments for each case
    args_list = [(code, case, time_limit) for case in cases]

    # use ProcessPoolExecutor for parallel execution
    if max_workers is None:
        max_workers = min(len(cases), processes)

    loop = asyncio.get_event_loop()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # use run_in_executor to make the blocking executor.map non-blocking
        results = await loop.run_in_executor(
            None,
            lambda: list(executor.map(_run_code_wrapper, args_list))
        )

    return results

def test_multi_code(
    codes: List[str],
    cases: List[str],
    time_limit: float = 2,
    max_workers: Optional[int] = None
) -> List[List[CodeResult]]:
    """
    Execute multiple codes against multiple test cases using process pool
    Returns results grouped by code (each code gets a list of results for all cases)
    """
    if not codes or not cases:
        return []

    # prepare all combinations of (code, case, time_limit)
    all_args = []
    code_indices = []

    for code_idx, code in enumerate(codes):
        for case in cases:
            all_args.append((code, case, time_limit))
            code_indices.append(code_idx)

    # use ProcessPoolExecutor for parallel execution
    if max_workers is None:
        max_workers = min(len(all_args), multiprocessing.cpu_count())

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        all_results = list(executor.map(_run_code_wrapper, all_args))

    # group results back by code
    results_by_code = [[] for _ in range(len(codes))]
    for i, result in enumerate(all_results):
        results_by_code[code_indices[i]].append(result)

    return results_by_code
        
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
    
def save_json(file_path: str, data: dict):
    """
    Save JSON data to file, creating parent directories if needed
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(file_path, "w"), indent=2)
    
def queue_result(func):
    """
    Decorator to put function result in a queue if queue is provided
    Useful for multiprocessing scenarios
    """
    @wraps(func)
    def wrapper(*args, queue=None, **kwargs):
        result = func(*args, **kwargs)
        if queue is not None:
            queue.put(result)
    return wrapper

# example usage for testing
if __name__ == '__main__':
    code = \
"""
outs = []
for i in range(1000000):
    outs.append(i)
print(outs[:100])
"""
    cases = ["1 2 3", "4 5 6"]
    outs = test_code_multi_cases(code, cases)
    for out in outs:
        print(out)
