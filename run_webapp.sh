#!/usr/bin/env bash
# This script runs the Matschia web application

echo "Starting Matschia Web Application..."

# Ensure virtual environment is activated if it exists
if [ -d "venv" ] || [ -d ".venv" ]; then
  if [ -d "venv" ]; then
    source venv/bin/activate
  else
    source .venv/bin/activate
  fi
  echo "Virtual environment activated"
fi

# Install dependencies if needed
pip3 install -r requirements.txt

# Run the Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
python3 app.py

# Deactivate virtual environment (this line won't execute until server is stopped)
if [ -n "$VIRTUAL_ENV" ]; then
  deactivate
fi
