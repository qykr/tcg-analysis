#!/usr/bin/env python3
"""
Main entry point to test response generation.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the test generation."""
    generation_dir = Path(__file__).parent / "generation"
    
    # Change to generation directory
    os.chdir(generation_dir)
    
    # Run the test script
    print("🧪 Starting test generation...")
    print("📁 Working from:", generation_dir.absolute())
    
    try:
        subprocess.run([sys.executable, "test_generation.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running test generation: {e}")

if __name__ == "__main__":
    main()