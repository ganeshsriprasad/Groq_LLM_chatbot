#!/bin/bash

echo "Starting GenAI Chatbot..."
echo

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo
    echo "IMPORTANT: Please edit .env file and add your Grok API key!"
    echo
    read -p "Press Enter to continue..."
fi

# Start the application
echo "Starting FastAPI server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
