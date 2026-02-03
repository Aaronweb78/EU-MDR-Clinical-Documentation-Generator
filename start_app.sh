#!/bin/bash

echo "Starting EU MDR Clinical Documentation Generator..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Run ./test_setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Warning: Ollama doesn't seem to be running"
    echo "   Start Ollama with: ollama serve"
    echo ""
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start Streamlit
echo "Starting Streamlit application..."
echo "Application will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py --server.fileWatcherType none

