@echo off
echo Starting GenAI Chatbot...
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy ".env.example" ".env"
    echo.
    echo IMPORTANT: Please edit .env file and add your Grok API key!
    echo.
    pause
)

REM Start the application
echo Starting FastAPI server...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
