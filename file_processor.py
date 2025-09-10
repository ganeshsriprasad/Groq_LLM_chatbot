import os
import mimetypes
from typing import Optional, Dict, Any
import base64
import tempfile
from pathlib import Path

class FileProcessor:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        
        # Supported file types
        self.supported_extensions = {
            # Text files
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv',
            # Documents
            '.pdf', '.doc', '.docx',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            # Code
            '.cpp', '.c', '.java', '.php', '.rb', '.go', '.rs', '.swift'
        }
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Save uploaded file and return file info"""
        # Generate safe filename
        safe_filename = self._generate_safe_filename(filename)
        file_path = os.path.join(self.upload_dir, safe_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Get file info
        file_info = {
            "filename": safe_filename,
            "original_filename": filename,
            "file_path": file_path,
            "size": len(file_content),
            "mime_type": mimetypes.guess_type(filename)[0],
            "extension": Path(filename).suffix.lower()
        }
        
        return file_info
    
    def process_file(self, file_info: Dict[str, Any]) -> str:
        """Process uploaded file and return text content or description"""
        extension = file_info["extension"]
        file_path = file_info["file_path"]
        
        try:
            if extension in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']:
                return self._read_text_file(file_path)
            elif extension == '.pdf':
                return self._process_pdf(file_path)
            elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return self._process_image(file_info)
            else:
                return f"File uploaded: {file_info['original_filename']} ({file_info['size']} bytes)\nFile type: {file_info['mime_type']}\n\nThis file type is supported but content analysis is not available yet."
        
        except Exception as e:
            return f"Error processing file {file_info['original_filename']}: {str(e)}"
    
    def _read_text_file(self, file_path: str) -> str:
        """Read text content from file"""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return f"File content:\n\n{content}"
            except UnicodeDecodeError:
                continue
        
        return "Could not decode file content. Binary file or unsupported encoding."
    
    def _process_pdf(self, file_path: str) -> str:
        """Process PDF file (basic implementation)"""
        # Note: For full PDF processing, you'd install pypdf2 or pdfplumber
        # For now, return basic info
        file_size = os.path.getsize(file_path)
        return f"PDF file uploaded successfully.\nFile size: {file_size} bytes\n\nNote: PDF text extraction requires additional libraries. Consider uploading the text content directly for analysis."
    
    def _process_image(self, file_info: Dict[str, Any]) -> str:
        """Process image file"""
        return f"Image uploaded: {file_info['original_filename']}\nSize: {file_info['size']} bytes\nFormat: {file_info['extension']}\n\nImage analysis capabilities would require computer vision models. The image has been saved and can be referenced in our conversation."
    
    def _generate_safe_filename(self, filename: str) -> str:
        """Generate safe filename with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        # Remove unsafe characters
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"{timestamp}_{safe_name}{ext}"
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        extension = Path(filename).suffix.lower()
        return extension in self.supported_extensions
    
    def get_file_list(self) -> list:
        """Get list of uploaded files"""
        files = []
        for filename in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                })
        return sorted(files, key=lambda x: x["modified"], reverse=True)
