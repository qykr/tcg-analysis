#!/usr/bin/env python3
"""
Main entry point to run the web application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the web application."""
    webapp_dir = Path(__file__).parent / "webapp"
    
    # Change to webapp directory
    os.chdir(webapp_dir)
    
    # Run the server
    print("🌐 Starting web application...")
    print("📁 Serving from:", webapp_dir.absolute())
    print("🔗 Open: http://127.0.0.1:5173/")
    print("\nPress Ctrl+C to stop")
    
    try:
        subprocess.run([sys.executable, "server.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web application stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running web application: {e}")

if __name__ == "__main__":
    main()
