from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None
    session_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

class FileUploadResponse(BaseModel):
    success: bool
    filename: str
    file_id: str
    content_preview: str
    error: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: str
    message_count: int

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]

class SessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    session_data: Optional[dict] = None
    error: Optional[str] = None
