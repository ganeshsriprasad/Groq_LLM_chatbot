from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
from datetime import datetime
import logging

from models import (
    ChatRequest, ChatResponse, HealthResponse, ChatMessage,
    FileUploadResponse, SessionListResponse, SessionResponse
)
from grok_client import GrokClient
from chat_history import ChatHistoryManager
from file_processor import FileProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GenAI Chatbot",
    description="A ChatGPT-like chatbot powered by Grok API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize Grok client
try:
    grok_client = GrokClient()
    logger.info("Grok client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Grok client: {e}")
    grok_client = None

# Initialize chat history manager
chat_history = ChatHistoryManager()

# Initialize file processor
file_processor = FileProcessor()

@app.get("/")
async def serve_chat_interface(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now()
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """
    Process chat messages and return AI response
    """
    if not grok_client:
        raise HTTPException(
            status_code=500, 
            detail="Grok client not initialized. Please check your API key."
        )
    
    try:
        # Get or create session
        session_id = chat_request.session_id
        if not session_id:
            session_id = chat_history.create_session()
        
        # Add user message to history
        chat_history.add_message(session_id, "user", chat_request.message)
        
        # Prepare messages for Grok API
        messages = []
        
        # Add conversation history
        for msg in chat_request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": chat_request.message
        })
        
        # Generate response
        response = await grok_client.generate_response(messages)
        
        # Add AI response to history
        chat_history.add_message(session_id, "assistant", response)
        
        return ChatResponse(
            response=response,
            success=True,
            session_id=session_id
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(
            response="I'm sorry, I encountered an error while processing your request. Please try again.",
            success=False,
            error=str(e),
            session_id=chat_request.session_id
        )

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("GenAI Chatbot starting up...")
    
    # Test Grok API connection
    if grok_client:
        try:
            is_connected = await grok_client.test_connection()
            if is_connected:
                logger.info("Successfully connected to Grok API")
            else:
                logger.warning("Could not connect to Grok API - check your API key")
        except Exception as e:
            logger.error(f"Error testing Grok API connection: {e}")

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), session_id: str = Form(None)):
    """Upload and process file"""
    try:
        # Check file size (limit to 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
        # Check if file type is supported
        if not file_processor.is_supported_file(file.filename):
            raise HTTPException(status_code=400, detail="File type not supported.")
        
        # Save and process file
        file_info = file_processor.save_uploaded_file(content, file.filename)
        content_preview = file_processor.process_file(file_info)
        
        # If session_id provided, add file content to chat history
        if session_id:
            file_message = f"📎 Uploaded file: {file.filename}\n\n{content_preview}"
            chat_history.add_message(session_id, "user", file_message)
        
        return FileUploadResponse(
            success=True,
            filename=file_info["filename"],
            file_id=file_info["filename"],
            content_preview=content_preview[:500] + ("..." if len(content_preview) > 500 else "")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return FileUploadResponse(
            success=False,
            filename=file.filename if file else "unknown",
            file_id="",
            content_preview="",
            error=str(e)
        )

@app.get("/api/sessions", response_model=SessionListResponse)
async def get_sessions():
    """Get all chat sessions"""
    try:
        sessions = chat_history.get_all_sessions()
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get specific chat session"""
    try:
        session_data = chat_history.load_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            success=True,
            session_id=session_id,
            session_data=session_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {str(e)}")
        return SessionResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session():
    """Create new chat session"""
    try:
        session_id = chat_history.create_session()
        return SessionResponse(
            success=True,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return SessionResponse(
            success=False,
            error=str(e)
        )

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete chat session"""
    try:
        success = chat_history.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@app.get("/api/sessions/{session_id}/export", response_class=PlainTextResponse)
async def export_session(session_id: str):
    """Export chat session as text file"""
    try:
        export_text = chat_history.export_session(session_id)
        if not export_text:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return export_text
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export session")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
