#!/bin/bash
# Simple startup script for RpiPrint
# This script activates the virtual environment and runs the Flask app

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting RpiPrint from $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    echo "   Please create it first: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found - using default configuration"
fi

# Start the application
echo "🌐 Starting Flask application..."
echo "   Press Ctrl+C to stop"
echo ""

# Run with python (not python3, since venv is activated)
python app_production.py
