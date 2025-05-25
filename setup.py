#!/usr/bin/env python3
"""
Initial setup script for Twitter Analysis Tool
This script installs required Python packages and Playwright browsers
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=================================================================")
    print("          Twitter Analysis Tool - Initial Setup                   ")
    print("=================================================================")
    
    # Check Python version
    print("\n🔍 Checking Python version...")
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        sys.exit(1)
    print(f"✅ Found Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Install required packages
    print("\n📦 Installing required Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Error installing packages. Please check your internet connection and try again.")
        sys.exit(1)
    
    # Install Playwright browsers
    print("\n🎭 Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright browsers installed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Error installing Playwright browsers.")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating .env file for API keys...")
        with open(env_file, "w") as f:
            f.write("# API keys for Twitter Analysis Tool\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
        print("✅ .env file created. Please update it with your API keys.")
    
    # Make Python scripts executable
    print("\n🔧 Making Python scripts executable...")
    python_scripts = ["tweet_scraper.py", "twitter_analyzer.py", "twitter_wrapper.py", "tweet_poster.py", "app.py"]
    for script in python_scripts:
        if Path(script).exists():
            os.chmod(script, 0o755)
    print("✅ Python scripts are now executable.")
    
    print("\n✅ Setup complete! You're ready to run the Twitter Analysis Tool.")
    print("   Run the tool with: ./run_twitter_analysis.sh")

if __name__ == "__main__":
    main()
