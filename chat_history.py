import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid

class ChatHistoryManager:
    def __init__(self, storage_dir: str = "chat_sessions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def create_session(self) -> str:
        """Create a new chat session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "title": "New Chat",
            "messages": []
        }
        self.save_session(session_id, session_data)
        return session_id
    
    def save_session(self, session_id: str, session_data: Dict):
        """Save session data to file"""
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load session data from file"""
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to session and update summary/title"""
        session_data = self.load_session(session_id)
        if session_data:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            session_data["messages"].append(message)

            # Generate a summary/title for the session
            session_data["title"] = self.summarize_session(session_data["messages"])

            self.save_session(session_id, session_data)

    def summarize_session(self, messages):
        """Use the first user message as the session title, or 'New Chat' if none."""
        if not messages:
            return "New Chat"
        for m in messages:
            if m["role"] == "user" and m["content"].strip():
                return m["content"][:60] + ("..." if len(m["content"]) > 60 else "")
        return "New Chat"
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all chat sessions metadata and update title with summary"""
        sessions = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # Remove .json extension
                session_data = self.load_session(session_id)
                if session_data:
                    # Always recompute the summary/title for sidebar
                    new_title = self.summarize_session(session_data.get("messages", []))
                    if session_data.get("title") != new_title:
                        session_data["title"] = new_title
                        self.save_session(session_id, session_data)
                    sessions.append({
                        "session_id": session_id,
                        "title": new_title,
                        "created_at": session_data.get("created_at"),
                        "message_count": len(session_data.get("messages", []))
                    })
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def export_session(self, session_id: str) -> Optional[str]:
        """Export session as formatted text"""
        session_data = self.load_session(session_id)
        if not session_data:
            return None
        
        export_text = f"Chat Session: {session_data.get('title', 'Untitled')}\n"
        export_text += f"Created: {session_data.get('created_at', 'Unknown')}\n"
        export_text += f"Messages: {len(session_data.get('messages', []))}\n"
        export_text += "=" * 50 + "\n\n"
        
        for msg in session_data.get("messages", []):
            role = "You" if msg["role"] == "user" else "AI"
            timestamp = msg.get("timestamp", "")
            export_text += f"[{timestamp}] {role}:\n{msg['content']}\n\n"
        
        return export_text
