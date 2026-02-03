#!/bin/bash

echo "================================"
echo "MDR Doc Generator - Setup Test"
echo "================================"
echo ""

# Check Python
echo "✓ Checking Python..."
python3 --version
echo ""

# Check if venv exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "✗ Virtual environment not found"
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi
echo ""

# Activate venv and install dependencies
echo "Installing dependencies..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip --quiet

echo "Installing requirements..."
pip install -r requirements.txt --quiet

echo ""
echo "✓ Dependencies installed!"
echo ""

# Check Ollama
echo "Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    ollama --version

    # Check if llama3 is pulled
    if ollama list | grep -q "llama3"; then
        echo "✓ llama3:8b model is available"
    else
        echo "✗ llama3:8b model not found"
        echo "  Run: ollama pull llama3:8b"
    fi
else
    echo "✗ Ollama is not installed"
    echo "  Install from: https://ollama.com/download"
fi
echo ""

# Test imports
echo "Testing Python imports..."
python3 << 'PYTHON_TEST'
import sys
try:
    import streamlit
    print("✓ Streamlit")
    import chromadb
    print("✓ ChromaDB")
    import sentence_transformers
    print("✓ Sentence Transformers")
    import ollama
    print("✓ Ollama")
    import pymupdf
    print("✓ PyMuPDF")
    from docx import Document
    print("✓ python-docx")
    import openpyxl
    print("✓ openpyxl")
    print("\n✓ All required packages installed!")
except ImportError as e:
    print(f"✗ Missing package: {e}")
    sys.exit(1)
PYTHON_TEST

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To run the application:"
echo "  1. source venv/bin/activate"
echo "  2. streamlit run app.py"
echo ""
