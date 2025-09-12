#!/usr/bin/env python3
"""
Setup script for SandboxFusion sandbox.
This script helps set up the SandboxFusion code execution environment.
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {cmd}")
        print(f"Error: {e.stderr}")
        return False

def check_sandbox_running(url="http://localhost:8080"):
    """Check if sandbox is already running."""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def setup_sandbox():
    """Set up SandboxFusion sandbox."""
    print("🚀 Setting up SandboxFusion sandbox...")
    
    # Check if sandbox is already running
    if check_sandbox_running():
        print("✅ SandboxFusion is already running!")
        return True
    
    # Clone SandboxFusion if not exists
    sandbox_dir = Path("SandboxFusion")
    if not sandbox_dir.exists():
        print("📥 Cloning SandboxFusion repository...")
        if not run_command("git clone https://github.com/bytedance/SandboxFusion.git"):
            print("❌ Failed to clone SandboxFusion repository")
            return False
    else:
        print("✅ SandboxFusion directory already exists")
    
    # Build Docker images
    print("🐳 Building Docker images...")
    if not run_command("docker build -f ./scripts/Dockerfile.base -t code_sandbox:base .", cwd=sandbox_dir):
        print("❌ Failed to build base Docker image")
        return False
    
    # Update Dockerfile.server to use the base image
    dockerfile_path = sandbox_dir / "scripts" / "Dockerfile.server"
    if dockerfile_path.exists():
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        if "FROM code_sandbox:base" not in content:
            content = "FROM code_sandbox:base\n" + content
            with open(dockerfile_path, 'w') as f:
                f.write(content)
    
    if not run_command("docker build -f ./scripts/Dockerfile.server -t code_sandbox:server .", cwd=sandbox_dir):
        print("❌ Failed to build server Docker image")
        return False
    
    # Run the sandbox
    print("🚀 Starting SandboxFusion server...")
    if not run_command("docker run -d --rm --privileged -p 8080:8080 --name sandbox-fusion code_sandbox:server make run-online", cwd=sandbox_dir):
        print("❌ Failed to start SandboxFusion server")
        return False
    
    # Wait for sandbox to be ready
    print("⏳ Waiting for sandbox to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        if check_sandbox_running():
            print("✅ SandboxFusion is ready!")
            return True
        time.sleep(1)
        print(f"   Waiting... ({i+1}/30)")
    
    print("❌ SandboxFusion failed to start within 30 seconds")
    return False

def main():
    """Main setup function."""
    print("🔧 SandboxFusion Setup Script")
    print("=" * 40)
    
    # Check if Docker is installed
    if not run_command("docker --version"):
        print("❌ Docker is not installed. Please install Docker first.")
        print("   Visit: https://docs.docker.com/get-docker/")
        return False
    
    # Check if Docker is running
    if not run_command("docker info"):
        print("❌ Docker is not running. Please start Docker first.")
        return False
    
    # Set up sandbox
    if setup_sandbox():
        print("\n🎉 Setup complete!")
        print("📝 SandboxFusion is running at: http://localhost:8080")
        print("🔧 You can now run the generation scripts with code execution.")
        return True
    else:
        print("\n❌ Setup failed!")
        print("💡 Try running the commands manually:")
        print("   1. git clone https://github.com/bytedance/SandboxFusion.git")
        print("   2. cd SandboxFusion")
        print("   3. docker build -f ./scripts/Dockerfile.base -t code_sandbox:base .")
        print("   4. docker build -f ./scripts/Dockerfile.server -t code_sandbox:server .")
        print("   5. docker run -d --rm --privileged -p 8080:8080 code_sandbox:server make run-online")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
