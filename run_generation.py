#!/usr/bin/env python3
"""
Main entry point to run response generation.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the response generation."""
    generation_dir = Path(__file__).parent / "generation"
    
    # Change to generation directory
    os.chdir(generation_dir)
    
    # Run the generation script
    print("🤖 Starting response generation...")
    print("📁 Working from:", generation_dir.absolute())
    
    try:
        subprocess.run([sys.executable, "run_generation.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running generation: {e}")

if __name__ == "__main__":
    main()