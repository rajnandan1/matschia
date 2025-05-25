#!/bin/bash

# run_twitter_analysis.sh - A script to run Twitter data collection and analysis
# Created on: May 23, 2025

# Display banner and welcome message
echo "=================================================================="
echo "             Twitter Data Collection & Analysis Tool              "
echo "=================================================================="
echo "This script will:"
echo "1. Collect Twitter posts using Python Playwright"
echo "2. Analyze the collected posts to find the most engaging content"
echo "3. Generate witty replies for engagement"
echo "=================================================================="

# Set the working directory to the script's directory
cd "$(dirname "$0")"

# Check for required dependencies
echo "🔍 Checking dependencies..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Install Python dependencies if needed
echo "📦 Ensuring Python dependencies are installed..."
python3 -m pip install -r requirements.txt

# Install Playwright browsers
echo "📦 Installing Playwright browsers..."
python3 -m playwright install chromium

# Step 1: Collect data using Playwright script
echo -e "\n🔄 Step 1: Starting Twitter data collection with Playwright..."
echo "📱 A Chrome window will open. You may need to log in if no saved session exists."
echo "⚠️  Please do not close the Chrome window during data collection."

# Run the Python Playwright collection script and capture its PID
python3 tweet_scraper.py &
PLAYWRIGHT_PID=$!

# Function to check if data.json has been created and has content
check_data_file() {
    if [ -f "data.json" ] && [ -s "data.json" ]; then
        # Check if the file contains valid JSON with at least one entry
        if jq -e '. | length > 0' data.json &>/dev/null; then
            return 0 # Success
        fi
    fi
    return 1 # File doesn't exist, is empty, or has invalid JSON
}

# Wait for data collection to complete
echo "⏳ Waiting for data collection to complete..."
MAX_WAIT=300 # Maximum wait time in seconds
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    # Check if data.json has been created with content
    if check_data_file; then
        echo "✅ Data collection complete! Twitter posts saved to data.json"
        break
    fi
    
    # Check if the process is still running
    if ! kill -0 $PLAYWRIGHT_PID 2>/dev/null; then
        echo "⚠️  Playwright process has ended"
        if check_data_file; then
            echo "✅ Data.json file found with content"
            break
        else
            echo "❌ Data collection may have failed. Check for errors above."
            exit 1
        fi
    fi
    
    # Wait and increment counter
    sleep 5
    WAITED=$((WAITED + 5))
    echo -n "." # Show progress
done

# If we've waited too long, prompt the user
if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "\n⚠️  Data collection is taking longer than expected."
    read -p "Continue waiting for data collection? (y/n): " CONTINUE
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        echo "❌ Aborting analysis. Try running the scripts individually."
        exit 1
    fi
fi

# Step 2: Run Twitter analysis
echo -e "\n🔄 Step 2: Starting Twitter analysis with AI agents..."
python3 twitter_analyzer.py

# Check if analysis results were created
if [ -f "analysis_results.json" ]; then
    echo -e "\n✅ Analysis complete! Results saved to analysis_results.json"
    
    # Display a summary of the results
    echo -e "\n📊 Summary of analysis:"
    echo "----------------------------------------"
    jq -r '"Total tweets analyzed: " + (.analysis_summary.total_tweets|tostring)' analysis_results.json
    jq -r '"Tech tweets found: " + (.analysis_summary.tech_tweets_found|tostring)' analysis_results.json
    jq -r '"Best engagement score: " + (.analysis_summary.best_score|tostring)' analysis_results.json
    echo "----------------------------------------"
    echo -e "Best tweet: "
    jq -r '.best_tweet.post' analysis_results.json
    echo "----------------------------------------"
    echo -e "Generated reply: "
    jq -r '.generated_reply.text' analysis_results.json
    echo "----------------------------------------"
else
    echo "❌ Analysis may have failed. Check for errors above."
fi

echo -e "\n✨ All done! You can find detailed results in analysis_results.json"
