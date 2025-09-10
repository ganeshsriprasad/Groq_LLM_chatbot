# GenAI Chatbot

A modern ChatGPT-like chatbot built with FastAPI backend and vanilla JavaScript frontend, powered by Grok API.

https://github.com/ganeshsriprasad/Groq_LLM_chatbot/blob/f48ca32147b7d29da85703cd618d255127285990/image.png

![groq-llm-chatscreen]([https://github.com/AnumMujahid/netflix-clone/blob/master/n1.png](https://github.com/ganeshsriprasad/Groq_LLM_chatbot/blob/f48ca32147b7d29da85703cd618d255127285990/image.png))

## Features

- 🤖 AI-powered conversations using Grok API
- 💬 Real-time chat interface similar to ChatGPT
- 🚀 FastAPI backend with async support
- 📱 Responsive design for desktop and mobile
- 🔒 Secure API key management
- ⚡ Fast and lightweight

## Quick Start

1. **Clone and setup**:
   ```bash
   cd genai-chatbot
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Add your Grok API key to .env file
   ```

3. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

4. **Open your browser**:
   Navigate to `http://localhost:8000`

## Environment Variables

Create a `.env` file with:
```
GROK_API_KEY=your_grok_api_key_here
GROK_API_BASE=https://api.x.ai/v1
```

## API Endpoints

- `GET /` - Serve the chat interface
- `POST /api/chat` - Send message to AI and get response
- `GET /api/health` - Health check endpoint

## Project Structure

```
genai-chatbot/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── grok_client.py       # Grok API client
├── static/
│   ├── style.css        # Frontend styles
│   └── script.js        # Frontend JavaScript
├── templates/
│   └── index.html       # Chat interface
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## Contributing

Feel free to submit issues and enhancement requests!
